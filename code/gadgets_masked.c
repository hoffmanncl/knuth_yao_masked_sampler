#include "masked.h"
#include "gadgets_masked.h"
#include "bench.h"

/*************************************************
 * Name:        transpose32
 *
 * Description: perform a bit transposition inplace
 *
 * Arguments: - uint32_t[32] a: bitmatrix to transpose inplace
 **************************************************/
void transpose32(uint32_t a[32]) {
    int j, k;
    uint32_t m, t;
    
    m = 0x0000FFFF;
    for (j = 16; j != 0; j = j >> 1, m = m ^ (m << j)) {
        for (k = 0; k < 32; k = (k + j + 1) & ~j) {
            t = (a[k + j] ^ (a[k] >> j)) & m;
            a[k + j] = a[k + j] ^ t;
            a[k] = a[k] ^ (t << j);
        }
    }
}

/*************************************************
 * MASKING UTILITIES
 **************************************************/

void trivial_mask(uint32_t *output, uint32_t cst) {
    output[0] = cst;
    for (size_t i = 1; i < NSHARES; i++) {
        output[i] = 0;
    }
}

void mask(uint32_t *output, uint32_t cst) {
    output[0] = cst;
    for (size_t i = 1; i < NSHARES; i++) {
        uint32_t r = get_random();
        output[0] ^= r;
        output[i] = r;
    }
}

void unmask(uint32_t *output, uint32_t *in) {
    *output = in[0];
    for (size_t i = 1; i < NSHARES; i++) {
        *output ^= in[i];
    }
}

/*************************************************
 * CORE LOGIC GATES
 **************************************************/
inline void masked_and_core(uint32_t *output, uint32_t *in1, uint32_t *in2) {
    masked_and_c(NSHARES, output, 1, in1, 1, in2, 1);
}

inline void masked_and_cst_core(uint32_t *output, uint32_t *in1, uint32_t cst) {
    for (size_t i = 0; i < NSHARES; i++) {
        output[i] = in1[i] & cst;
    }
}

inline void masked_xor_core(uint32_t *output, uint32_t *in1, uint32_t *in2) {
    masked_xor_c(NSHARES, output, 1, in1, 1, in2, 1);
}

inline void masked_not_core(uint32_t *output, uint32_t *in) {
    output[0] = ~in[0];
    for (size_t i = 1; i < NSHARES; i++) {
        output[i] = in[i];
    }
}

void masked_copy_core(uint32_t *output, uint32_t *in) {
    for (size_t i = 0; i < NSHARES; i++) {
        output[i] = in[i];
    }
}

/*************************************************
 * ARITHMETIC & SIGNS
 **************************************************/
void masked_full_adder(uint32_t *output_s, uint32_t *output_c, uint32_t *in1, uint32_t *in2, uint32_t *in3) {
    uint32_t tmp1[NSHARES], tmp2[NSHARES], tmp3[NSHARES];
    
    masked_xor_core(tmp1, in1, in2);      // tmp1 = in1 ^ in2
    masked_xor_core(output_s, tmp1, in3); // s = tmp1 ^ in3 = (in1 ^ in2) ^ in3
    masked_xor_core(tmp2, in1, in3);      // tmp2 = in1 ^ in3
    masked_and_core(tmp3, tmp2, tmp1);    // tmp3 = tmp2 & tmp1 = ((in1 ^ in2) ^ in3) & (in1 ^ in3)
    masked_xor_core(output_c, in1, tmp3); // c = in1 ^ tmp3 = in1 ^ ((in1 ^ in2) ^ in3) & (in1 ^ in3))
}

void masked_add_signs(uint32_t *output, uint32_t *in, uint32_t *signs) {
    uint32_t out[OUTPUT_SIZE * NSHARES];
    
    // Apply conditional 1s-complement via XOR
    for (size_t i = 0; i < OUTPUT_SIZE; i++) {
        masked_xor_core(out + i * NSHARES, in + i * NSHARES, signs);
    }

    uint32_t mc[NSHARES], mzero[NSHARES];
    trivial_mask(mc, 0);
    trivial_mask(mzero, 0);
    
    // Add the sign bit as carry-in to complete the 2s-complement conversion
    masked_full_adder(output + 0 * NSHARES, mc, out + 0 * NSHARES, signs, mc);
    
    for (size_t i = 1; i < OUTPUT_SIZE - 1; i++) {
        masked_full_adder(output + i * NSHARES, mc, out + i * NSHARES, mzero, mc);
    }

    masked_xor_core(output + (OUTPUT_SIZE - 1) * NSHARES, out + (OUTPUT_SIZE - 1) * NSHARES, mc);
}

/*************************************************
 * WRAPPER
 **************************************************/
void masked_sampler(ky_circuit_func circuit, uint32_t *output, uint32_t *rs, size_t precision) {
    // 1. Evaluate the generated Knuth-Yao circuit
    circuit(output, rs);

    // 2. Apply signs
    // The randomness array 'rs' must contain (precision + 1) * NSHARES elements.
    uint32_t *signs = rs + precision * NSHARES;
    
    masked_add_signs(output, output, signs);
}
