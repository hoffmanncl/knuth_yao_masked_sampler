import sys

# Paramètre HAWK_256_T0 de ton generate_circuit.py
spec = [
    0x26B871FBD58485D45050, 0x07C054114F1DC2FA7AC9, 0x00A242F74ADDA0B5AE61,
    0x0005252E2152AB5D758B, 0x00000FDE62196C1718FC, 0x000000127325DDF8CEBA,
    0x0000000008100822C548, 0x00000000000152A6E9AE, 0x0000000000000014DA4A,
    0x0000000000000000007B
]
precision = 78

# 1. Calcul de la PMF (Identique à ton generate_circuit.py)
pmf = []
pmf.append((1 << precision) - spec[0])
for i in range(len(spec) - 1):
    pmf.append(spec[i] - spec[i+1])
pmf.append(spec[-1])

# 2. Reconstruction des préfixes de l'arbre Knuth-Yao
paths_by_value = {x: [] for x in range(len(pmf))}
node_val = 0
for d in range(1, precision + 1):
    for x in range(len(pmf)):
        if (pmf[x] >> (precision - d)) & 1:
            paths_by_value[x].append((node_val, d))
            node_val += 1
    node_val *= 2

# 3. Calcul des bornes exactes (Edges) de chaque feuille
edges_set = set([0, (1 << precision) - 1])
for x, paths in paths_by_value.items():
    for p, d in paths:
        # p est le préfixe sur d bits. 
        # On le décale pour obtenir l'entier sur 'precision' bits.
        start_val = p << (precision - d)
        end_val = ((p + 1) << (precision - d)) - 1
        
        edges_set.add(start_val)
        edges_set.add(end_val)
        if start_val > 0:
            edges_set.add(start_val - 1)
        if end_val < (1 << precision) - 1:
            edges_set.add(end_val + 1)

edges = sorted(list(edges_set))

# 4. Simulation du résultat attendu pour ces Edges
expected_outputs = []
for val in edges:
    # On simule le parcours de l'arbre pour cette valeur
    out_val = -1
    for x, paths in paths_by_value.items():
        for p, d in paths:
            # Si le préfixe de 'val' correspond à 'p'
            if (val >> (precision - d)) == p:
                out_val = x
                break
        if out_val != -1: break
    expected_outputs.append(out_val)

# Padding pour remplir des batchs de 32 (Bitslicing)
while len(edges) % 32 != 0:
    edges.append(0)
    expected_outputs.append(expected_outputs[0])

batches = []
for i in range(0, len(edges), 32):
    batch_vals = edges[i:i+32]
    batch_exps = expected_outputs[i:i+32]
    # On teste avec Signe = 0 (Positif) puis Signe = 1 (Négatif)
    batches.append((batch_vals, batch_exps, 0))
    batches.append((batch_vals, [-x for x in batch_exps], 0xFFFFFFFF))

# 5. Écriture du fichier header
with open("ky_edge_vectors.h", "w") as f:
    f.write(f"#define NUM_EDGE_BATCHES {len(batches)}\n\n")
    f.write("static const uint32_t edge_bs_inputs[NUM_EDGE_BATCHES][79] = {\n")
    for vals, exps, sign_mask in batches:
        f.write("  {\n    ")
        bs = [0]*78
        for bit in range(78):
            w = 0
            for lane in range(32):
                # Attention : le MSB est généré en premier dans le Knuth-Yao
                # Donc on mappe le bit i (de 0 à 77) au bit d'index (77-i) de la valeur entière
                if (vals[lane] >> (77 - bit)) & 1:
                    w |= (1 << lane)
            bs[bit] = w
        bs.append(sign_mask)
        f.write(", ".join(f"0x{x:08X}" for x in bs))
        f.write("\n  },\n")
    f.write("};\n\n")

    f.write("static const int32_t edge_expected[NUM_EDGE_BATCHES][32] = {\n")
    for vals, exps, sign_mask in batches:
        f.write("  {\n    ")
        f.write(", ".join(str(x) for x in exps))
        f.write("\n  },\n")
    f.write("};\n")

print(f"Génération terminée : ky_edge_vectors.h ({len(batches)} batchs créés).")