"""
Knuth-Yao masked sampler circuit generator.

Given a discrete distribution specified at a fixed binary precision, this script
builds the corresponding DDG (discrete distribution generating) tree, emits a
bitsliced Boolean circuit evaluating it with one AND per internal node, minimizes
its linear (XOR) part, and writes a masked C implementation (ky_samplers.{c,h}).

--------------------------------------------------------------------------------
ADDING A NEW DISTRIBUTION
--------------------------------------------------------------------------------
Append an entry to the `parameters` list with three fields:

    "name":      identifier used for the generated C symbols and file sections.
    "precision": number n of fractional bits the distribution is given at. Every
                 probability is an integer multiple of 2^-n, and the DDG tree has
                 depth n. This is the bit-length of the input randomness consumed
                 per sample; sign handling is applied separately.
    "spec":      the distribution, given as a list of non-negative integers. Two
                 input conventions are accepted, selected by the name (see the
                 "PMF Generation" block below):

      - FRODO-style (name contains "frodo"): a table of the *half* distribution.
        spec[0] is the (doubled) weight of the zero value and is halved here to
        account for the sign bit; spec[1:] are the weights of the positive
        support. The values are the unnormalized PMF, i.e. integers p_x such that
        sum(p_x) = 2^n.

      - HAWK-style (name contains "hawk"): the reverse CDT (RCDT), i.e. the list
        of tail probabilities T[i] = Pr[X > i], each a fixed-point integer scaled
        by 2^n. The PMF is recovered here by finite differences
        (p_i = T[i-1] - T[i]), with the endpoints handled explicitly.

    In both cases the entry is converted to an unnormalized PMF stored in
    p["pmf"], a list of integers summing to exactly 2^precision. If your
    distribution is neither FRODO- nor HAWK-shaped, provide the PMF in that form
    directly and add a matching branch in the "PMF Generation" block below (or
    set p["pmf"] yourself and skip the conversion).
    It is also possible to directly add the pnf in the "pmf" field.

--------------------------------------------------------------------------------
REQUIREMENTS AND SANITY CHECKS
--------------------------------------------------------------------------------
    - The PMF must sum to 2^precision exactly (an incomplete tree is a bug, not a
      truncation).
    - Only the half distribution is sampled; the sign is applied afterwards, so
      the zero value must already be scaled accordingly (this is what the FRODO
      branch does by halving spec[0]).
    - The cost scales with the total Hamming weight of the p_x expansions, not
      with the support size: sparse, narrow distributions are cheap, near-uniform
      ones are not.

Run `python generate_circuit.py` to (re)generate the C files for every entry.
"""

from math import log2, ceil
import os

parameters = [
    {
        "name": "frodo640 ",
        "precision": 15,
        "spec": [9288, 8720, 7216, 5264, 3384, 1918, 958, 422, 164, 56, 17, 4, 1]
    },
    {
        "name": "frodo976 ",
        "precision": 15,
        "spec": [11278, 10277, 7774, 4882, 2545, 1101, 396, 118, 29, 6, 1]
    },
    {
        "name": "frodo1344",
        "precision": 15,
        "spec": [18286, 14320, 6876, 2023, 364, 40, 2]
    },
    {
        "name": "hawk256_T0",
        "precision": 78,
        "spec": [
            0x26B871FBD58485D45050, 0x07C054114F1DC2FA7AC9, 0x00A242F74ADDA0B5AE61,
            0x0005252E2152AB5D758B, 0x00000FDE62196C1718FC, 0x000000127325DDF8CEBA,
            0x0000000008100822C548, 0x00000000000152A6E9AE, 0x0000000000000014DA4A,
            0x0000000000000000007B
        ]
    },
    {
        "name": "hawk256_T1",
        "precision": 78,
        "spec": [
            0x13459408A4B181C718B1, 0x027D614569CC54722DC9, 0x0020951C5CDCBAFF49A3,
            0x0000A3460C30AC398322, 0x000001355A8330C44097, 0x00000000DC8DE401FD12,
            0x00000000003B0FFB28F0, 0x00000000000005EFCD99, 0x00000000000000003953,
            0x00000000000000000000
        ]
    },
    {
        "name": "hawk512_T0",
        "precision": 78,
        "spec": [
            0x2C058C27920A04F8F267, 0x0E9A1C4FF17C204AA058, 0x02DBDE63263BE0098FFD,
            0x005156AEDFB0876A3BD8, 0x0005061E21D588CC61CC, 0x00002BA568D92EEC18E7,
            0x000000CF0F8687D3B009, 0x0000000216A0C344EB45, 0x0000000002EDF0B98A84,
            0x0000000000023AF3B2E7, 0x00000000000000EBCC6A, 0x000000000000000034CF,
            0x00000000000000000006
        ]
    },
    {
        "name": "hawk512_T1",
        "precision": 78,
        "spec": [
            0x1AFCBC689D9213449DC9, 0x06EBFB908C81FCE3524F, 0x01064EBEFD8FF4F07378,
            0x0015C628BC6B23887196, 0x0000FF769211F07B326F, 0x00000668F461693DFF8F,
            0x0000001670DB65964485, 0x000000002AB6E11C2552, 0x00000000002C253C7E81,
            0x00000000000018C14ABF, 0x0000000000000007876E, 0x0000000000000000013D,
            0x00000000000000000000
        ]
    },
    {
        "name": "hawk1024_T0",
        "precision": 78,
        "spec": [
            0x2C583AAA2EB76504E560, 0x0F1D70E1C03E49BB683E, 0x031955CDA662EF2D1C48,
            0x005E31E874B355421BB7, 0x000657C0676C029895A7, 0x00003D4D67696E51F820,
            0x0000014A1A8A93F20738, 0x00000003DAF47E8DFB21, 0x0000000006634617B3FF,
            0x000000000005DBEFB646, 0x00000000000002F93038, 0x0000000000000000D5A7,
            0x00000000000000000021
        ]
    },
    {
        "name": "hawk1024_T1",
        "precision": 78,
        "spec": [
            0x1B7F01AE2B17728DF2DE, 0x07506A00B82C69624C93, 0x01252685DB30348656A4,
            0x001A430192770E205503, 0x00015353BD4091AA96DB, 0x000009915A53D8667BEE,
            0x00000026670030160D5F, 0x00000000557CD1C5F797, 0x00000000006965E15B13,
            0x00000000000047E9AB38, 0x000000000000001B2445, 0x000000000000000005AA,
            0x00000000000000000000
        ]
    },
    {
        # Falcon / FN-DSA BaseSampler: half-Gaussian with sigma_max = 1.8205,
        # RCDT with 18 entries at 72-bit precision. Values are the `dist[]`
        # table of gaussian0_sampler in the Falcon reference implementation
        # (also PQClean, crypto_sign/falcon-512/clean/sign.c), with the three
        # 24-bit limbs recombined as hi*2^48 + mid*2^24 + lo. RCDT semantics
        # are identical to HAWK's: spec[i] = Pr[X > i] * 2^72, support
        # {0,...,18}. The sign and the variable center are handled by
        # SamplerZ, outside the base sampler, hence sign_bits = 0.
        "name": "falcon_base",
        "precision": 72,
        "sign_bits": 0,
        "spec": [
            0xA3F7F42ED3AC391802, 0x54D32B181F3F7DDB82, 0x227DCDD0934829C1FF,
            0x0AD1754377C7994AE4, 0x0295846CAEF33F1F6F, 0x00774AC754ED74BD5F,
            0x001024DD542B776AE4, 0x0001A1FFDC65AD63DA, 0x00001F80D88A7B6428,
            0x000001C3FDB2040C69, 0x00000012CF24D031FB, 0x00000000949F8B091F,
            0x0000000003665DA998, 0x00000000000EBF6EBB, 0x0000000000002F5D7E,
            0x000000000000007098, 0x0000000000000000C6, 0x000000000000000001
        ]
    },
    {
        # HAETAE base Gaussian: the CDT[64] table of sample_gauss16 in the
        # reference implementation (v1.1.2, src/sampler.c). This is a FORWARD
        # CDT sampled as z = #{i : rand16 > CDT[i]} on 16 uniform bits, so the
        # PMF is p_0 = CDT[0]+1, p_i = CDT[i]-CDT[i-1], p_64 = 2^16-1-CDT[63]
        # (support {0,...,64}, sigma_base ~ 2^4). It is the high-order part of
        # HAETAE's sigma = 2^76 fixed-point Gaussian (72 uniform low bits and
        # a Bernoulli-exp correction are applied on top, and the sign is drawn
        # separately in sample_gauss_N), hence sign_bits = 0.
        "name": "haetae_base",
        "precision": 16,
        "sign_bits": 0,
        "spec": [
            3266,  6520,  9748,  12938, 16079, 19159, 22168, 25096, 27934,
            30674, 33309, 35833, 38241, 40531, 42698, 44742, 46663, 48460,
            50135, 51690, 53128, 54454, 55670, 56781, 57794, 58712, 59541,
            60287, 60956, 61554, 62085, 62556, 62972, 63337, 63657, 63936,
            64178, 64388, 64569, 64724, 64857, 64970, 65066, 65148, 65216,
            65273, 65321, 65361, 65394, 65422, 65444, 65463, 65478, 65490,
            65500, 65508, 65514, 65519, 65523, 65527, 65529, 65531, 65533,
            65534
        ]
    }
]

# ==========================================
# PMF Generation
# ==========================================

for p in parameters:
    name = p["name"].lower()

    if "frodo" in name:
        pmf = [p["spec"][0] // 2] + p["spec"][1:]
        p["pmf"] = pmf
        
    elif "hawk" in name or "falcon" in name:
        rcdt = p["spec"]
        precision = p["precision"]
        pmf = []
        
        pmf.append((1 << precision) - rcdt[0])
        for i in range(len(rcdt) - 1):
            pmf.append(rcdt[i] - rcdt[i+1])
        pmf.append(rcdt[-1])
        
        p["pmf"] = pmf

    elif "haetae" in name:
        cdt = p["spec"]
        precision = p["precision"]
        pmf = [cdt[0] + 1]
        pmf += [cdt[i] - cdt[i - 1] for i in range(1, len(cdt))]
        pmf.append((1 << precision) - 1 - cdt[-1])
        p["pmf"] = pmf

for p in parameters:
    assert sum(p["pmf"]) == 1 << p["precision"], f"PMF of {p['name']} does not sum to 2^precision"
    assert all(w >= 0 for w in p["pmf"]), f"negative weight in PMF of {p['name']}"

# ==========================================
# FLAT MAPPER
# ==========================================

def build_flat_matrix_fast(pmf, precision):
    paths_by_value = {x: [] for x in range(len(pmf))}
    node_val = 0
    for d in range(1, precision + 1):
        for x in range(len(pmf)):
            if (pmf[x] >> (precision - d)) & 1:
                paths_by_value[x].append((node_val, d))
                node_val += 1
        node_val *= 2
        
    prefixes = set()
    for x, paths in paths_by_value.items():
        for p, d in paths:
            for prefix_len in range(d):
                prefixes.add((p >> (d - prefix_len), prefix_len))
                
    prefixes_by_depth = {d: [] for d in range(precision)}
    for val, d in prefixes:
        prefixes_by_depth[d].append((val, d))
        
    hw_nodes = { (0, 0): {0} } 
    gate_counter = 1
    
    for d in range(precision):
        for u in prefixes_by_depth[d]:
            val_d, _ = u
            u_right = (val_d * 2 + 1, d + 1)
            u_left = (val_d * 2, d + 1)
            
            hw_nodes[u_right] = {gate_counter}
            hw_nodes[u_left] = hw_nodes[u] ^ hw_nodes[u_right]
            
            gate_counter += 1
            
    max_val = max(paths_by_value.keys())
    out_bits = max_val.bit_length() if max_val > 0 else 1
    y_equations = {j: set() for j in range(out_bits)}
    
    for x, paths in paths_by_value.items():
        for j in range(out_bits):
            if (x >> j) & 1:
                for p, d in paths:
                    y_equations[j] ^= hw_nodes[(p, d)]
                    
    total_ands = max(0, gate_counter - 2)
    return y_equations, total_ands

# ==========================================
# XOR OPTIMIZER (SLP - DETERMINISTIC)
# ==========================================

def optimize_xor_slp(y_equations):
    # Sort key: numeric suffix first, then the full name. The full name breaks
    # ties between wires sharing a suffix (A_37, L_37, X_37), so the output no
    # longer depends on set iteration order, i.e. on Python's string hashing.
    _sort_cache = {}
    def sk(s):
        if s not in _sort_cache:
            parts = str(s).split('_')
            num = int(parts[-1]) if len(parts) > 1 and parts[-1].isdigit() else -1
            _sort_cache[s] = (num, str(s))
        return _sort_cache[s]

    targets = {}
    for j, eq in y_equations.items():
        if eq:
            targets[f"y_{j}"] = set([f"A_{g}" if isinstance(g, int) else str(g) for g in eq])
        else:
            targets[f"y_{j}"] = {"0"}

    instructions = []
    temp_counter = 1
    
    while True:
        pair_counts = {}
        for eq_set in targets.values():
            if len(eq_set) < 2:
                continue
            
            eq_list = sorted(eq_set, key=sk)
            for i in range(len(eq_list)):
                for k in range(i + 1, len(eq_list)):
                    pair = (eq_list[i], eq_list[k])
                    pair_counts[pair] = pair_counts.get(pair, 0) + 1
                    
        if not pair_counts:
            break
            
        max_cnt = max(pair_counts.values())
        if max_cnt <= 1:
            break
            
        best_pairs = [p for p, c in pair_counts.items() if c == max_cnt]
        best_pairs.sort(key=lambda p: (sk(p[0]), sk(p[1])))
        best_pair = best_pairs[0]
        
        new_signal = f"X_{temp_counter}"
        temp_counter += 1
        instructions.append((new_signal, best_pair[0], best_pair[1]))
        
        for eq_set in targets.values():
            if best_pair[0] in eq_set and best_pair[1] in eq_set:
                eq_set.remove(best_pair[0])
                eq_set.remove(best_pair[1])
                eq_set.add(new_signal)

    for j in sorted(targets.keys(), key=sk):
        eq_set = targets[j]
        while len(eq_set) > 1:
            eq_list = sorted(eq_set, key=sk)
            a, b = eq_list[0], eq_list[1]
            eq_set.remove(a)
            eq_set.remove(b)
            
            new_signal = f"X_{temp_counter}"
            temp_counter += 1
            instructions.append((new_signal, a, b))
            eq_set.add(new_signal)
                
    final_assignments = {k: sorted(list(v), key=sk)[0] if v else "0" for k, v in targets.items()}
    return instructions, final_assignments, len(instructions)


# ==========================================
# CIRCUIT GENERATOR (NETLIST)
# ==========================================

def generate_circuit_instructions(pmf, precision):
    paths_by_value = {x: [] for x in range(len(pmf))}
    node_val = 0
    for d in range(1, precision + 1):
        for x in range(len(pmf)):
            if (pmf[x] >> (precision - d)) & 1:
                paths_by_value[x].append((node_val, d))
                node_val += 1
        node_val *= 2

    prefixes = set()
    valid_leaves = set()
    for x, paths in paths_by_value.items():
        for p, d in paths:
            if x > 0:
                valid_leaves.add((p, d))
            for prefix_len in range(d):
                prefixes.add((p >> (d - prefix_len), prefix_len))

    prefixes_by_depth = {d: [] for d in range(precision)}
    for val, d in prefixes:
        prefixes_by_depth[d].append((val, d))

    wires = {(0, 0): "1"}
    tree_instructions = []
    gate_counter = 1

    for d in range(precision):
        for u in sorted(prefixes_by_depth[d], key=lambda item: item[0]):
            p_wire = wires[u]
            u_right = (u[0] * 2 + 1, d + 1)
            u_left = (u[0] * 2, d + 1)

            r_wire = f"A_{gate_counter}"
            
            # COPY optimization: Short-circuits the root AND gate
            if p_wire == "1":
                tree_instructions.append(f"{r_wire:<5} = COPY u_{d}")
            else:
                tree_instructions.append(f"{r_wire:<5} = {p_wire} AND u_{d}")
                
            wires[u_right] = r_wire

            if u_left in prefixes or u_left in valid_leaves:
                l_wire = f"L_{gate_counter}"
                
                # NOT optimization: Short-circuits the root XOR gate
                if p_wire == "1":
                    tree_instructions.append(f"{l_wire:<5} = NOT {r_wire}")
                else:
                    tree_instructions.append(f"{l_wire:<5} = {p_wire} XOR {r_wire}")
                    
                wires[u_left] = l_wire
                
            gate_counter += 1

    max_val = max(paths_by_value.keys())
    out_bits = max_val.bit_length() if max_val > 0 else 1
    y_equations = {j: set() for j in range(out_bits)}

    for x, paths in paths_by_value.items():
        if x == 0: continue
        for j in range(out_bits):
            if (x >> j) & 1:
                for p, d in paths:
                    y_equations[j].add(wires[(p, d)])

    slp_tuples, final_assignments_dict, _ = optimize_xor_slp(y_equations)
    
    slp_instructions = [f"{dest:<5} = {a} XOR {b}" for dest, a, b in slp_tuples]
    final_assignments = [f"{k:<5} = {v}" for k, v in sorted(final_assignments_dict.items())]

    return tree_instructions, slp_instructions, final_assignments


# ==========================================
# C CODE GENERATOR
# ==========================================

def export_c_files(parameters, c_filename="../code/ky_samplers.c", h_filename="../code/ky_samplers.h"):
    print(f"\nGenerating C files: {c_filename} and {h_filename}...")
    
    with open(h_filename, "w") as fh, open(c_filename, "w") as fc:
        fh.write("#ifndef KY_SAMPLERS_H\n#define KY_SAMPLERS_H\n\n")
        fh.write('#include "gadgets_masked.h"\n\n')
        
        fc.write(f'#include "{h_filename}"\n\n')

        for p in parameters:
            name = p["name"].strip().lower()
            precision = p["precision"]
            
            tree_inst, slp_inst, finals = generate_circuit_instructions(p["pmf"], precision)
            
            variables = set()
            for inst in tree_inst + slp_inst:
                dest = inst.split('=')[0].strip()
                variables.add(dest)
            
            func_name = f"masked_ky_sampler_{name}"
            # Uses raw uint32_t pointers for 1D arrays
            sig = f"void {func_name}(uint32_t *output, uint32_t *rs)"
            
            fh.write(f"{sig};\n")
            
            fc.write(f"{sig} {{\n")
            fc.write("    uint32_t const_0[NSHARES];\n")
            fc.write("    trivial_mask(const_0, 0);\n\n")
            
            if variables:
                vars_list = sorted(list(variables))
                for i in range(0, len(vars_list), 10):
                    fc.write("    uint32_t " + "[NSHARES], ".join(vars_list[i:i+10]) + "[NSHARES];\n")
            
            def sanitize(v):
                if v == "0": return "const_0"
                if v.startswith("u_"): 
                    idx = v.split('_')[1]
                    return f"rs + {idx} * NSHARES"
                return v

            fc.write("\n")
            for inst in tree_inst:
                dest, expr = [s.strip() for s in inst.split('=')]
                parts = expr.split()
                
                if len(parts) == 2 and parts[0] == "COPY":
                    fc.write(f"    masked_copy_core({dest}, {sanitize(parts[1])});\n")
                elif len(parts) == 2 and parts[0] == "NOT":
                    fc.write(f"    masked_not_core({dest}, {sanitize(parts[1])});\n")
                elif len(parts) == 3 and parts[1] == "AND":
                    fc.write(f"    masked_and_core({dest}, {sanitize(parts[0])}, {sanitize(parts[2])});\n")
                elif len(parts) == 3 and parts[1] == "XOR":
                    fc.write(f"    masked_xor_core({dest}, {sanitize(parts[0])}, {sanitize(parts[2])});\n")
            
            fc.write("\n")
            for inst in slp_inst:
                dest, expr = [s.strip() for s in inst.split('=')]
                parts = expr.split()
                fc.write(f"    masked_xor_core({dest}, {sanitize(parts[0])}, {sanitize(parts[2])});\n")
                
            fc.write("\n")
            for inst in finals:
                dest, expr = [s.strip() for s in inst.split('=')]
                parts = expr.split()
                bit_idx = dest.split('_')[1]
                fc.write(f"    masked_copy_core(output + {bit_idx} * NSHARES, {sanitize(parts[0])});\n")
                
            fc.write("}\n\n")
            
        fh.write("\n#endif // KY_SAMPLERS_H\n")

# ==========================================
# CDT COST MODEL ([AEHT26b, Sec. 4.1])
# ==========================================

def cdt_pivot_costs(pmf, precision, l):
    """SecAnd and SecXor cost of the CDT pivot evaluation of [AEHT26b].

    The pivot of level m is a flat ANF polynomial over the comparison bits,
    whose coefficients are public constants derived from the CDT. Building the
    2^(m-1) - 1 non-constant monomials of level m costs one 1-bit SecAnd each,
    i.e. 2^(l-1) - l SecAnd over the whole tree. Conditioning a public constant
    by such a monomial costs one SecXor per set bit of that constant, which is
    what this function counts (the benchmarked implementation conditions every
    bit, set or not, so the count is conservative towards CDT).
    """
    n = (1 << l) - 1

    # CDF - 1 table, padded with 2^precision - 1 beyond the support
    cdf_m1, acc = [], 0
    for i in range(n):
        if i < len(pmf):
            acc += pmf[i]
        cdf_m1.append(acc - 1)

    # flat binary search tree, level by level
    levels = [[] for _ in range(l)]

    def traverse(level, left, right):
        if left > right:
            return
        mid = (left + right) // 2
        levels[level].append(cdf_m1[mid])
        traverse(level + 1, left, mid - 1)
        traverse(level + 1, mid + 1, right)

    traverse(0, 0, n - 1)

    xor = 0
    for m, level_data in enumerate(levels):
        # Fast Moebius transform: ANF coefficients of the level
        anf = list(level_data)
        step = 1
        while step < len(anf):
            for i in range(0, len(anf), step * 2):
                for j in range(i, i + step):
                    anf[j + step] ^= anf[j]
            step *= 2
        for mask in range(1, 1 << m):   # non-constant monomials only
            xor += bin(anf[mask]).count("1")

    return (1 << (l - 1)) - l, xor


def sign_costs(q):
    """Cost of the conditional two's complement negation (masked_add_signs).

    q SecXor for the conditional one's complement, then q-1 full adders
    (1 SecAnd and 4 SecXor each, [BC22, Algorithm 5]), then one SecXor for the
    top bit, which needs no carry out.
    """
    if q == 0:
        return 0, 0
    return q - 1, 5 * q - 3


if __name__ == "__main__":
    
    header = f"{'Parameter Set':<15} | {'Prec.':<5} | {'KY ANDs':<8} | {'CDT ANDs':<8} | {'KY XORs':<8} | {'CDT XORs':<8} | {'KY tot':<7} | {'CDT tot':<7} | {'Diff AND':<8} | {'Diff XOR':<8} | {'Diff tot'}"
    print(header)
    print("-" * len(header))
    
    for p in parameters:
        pmf = p["pmf"]
        precision = p["precision"]
        name = p["name"].strip()
        
        # Gates of the circuit we emit and benchmark, sign application excluded.
        tree, slp, _ = generate_circuit_instructions(pmf, precision)
        total_ands_ky = sum(1 for i in tree if " AND " in i)
        total_xors_ky = sum(1 for i in tree if " XOR " in i) + len(slp)
        
        l = ceil(log2(len(pmf)))
        
        cdt_and_comparisons = l * precision
        cdt_xor_comparisons = 3 * l * precision
        cdt_and_pivot, cdt_xor_pivot = cdt_pivot_costs(pmf, precision, l)
        
        total_ands_cdt = cdt_and_comparisons + cdt_and_pivot
        total_xors_cdt = cdt_xor_comparisons + cdt_xor_pivot
        
        q = p.get("sign_bits", 4 if name == "frodo1344" else 5)
        sign_ands, sign_xors = sign_costs(q)
        
        total_ands_ky += sign_ands
        total_xors_ky += sign_xors
        
        total_ands_cdt += sign_ands
        total_xors_cdt += sign_xors
        
        diff_pct_xors = ((total_xors_ky - total_xors_cdt) / total_xors_cdt) * 100
        diff_pct_ands = ((total_ands_ky - total_ands_cdt) / total_ands_cdt) * 100
        
        tot_ky = total_ands_ky + total_xors_ky
        tot_cdt = total_ands_cdt + total_xors_cdt
        diff_pct_tot = ((tot_ky - tot_cdt) / tot_cdt) * 100
        
        print(f"{name:<15} | {precision:<5} | {total_ands_ky:<8} | {total_ands_cdt:<8} | {total_xors_ky:<8} | {total_xors_cdt:<8} | {tot_ky:<7} | {tot_cdt:<7} | {diff_pct_ands:>+7.1f}% | {diff_pct_xors:>+7.1f}% | {diff_pct_tot:>+6.1f}%")

    export_c_files(parameters)
    print("\nGeneration completed successfully!")
