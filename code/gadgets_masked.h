#ifndef GADGETS_MASKED_H
#define GADGETS_MASKED_H

#include "masked.h"
#include "out_gadgets_masked.h"
#include "stdint.h"
#include <stddef.h>


typedef uint32_t masked_uint32[NSHARES];

void transpose32(uint32_t a[32]);

void trivial_mask(uint32_t *output, uint32_t cst);
void mask(uint32_t *output, uint32_t cst);
void unmask(uint32_t *output, uint32_t *in);

// Core logic gates
void masked_and_core(uint32_t *output, uint32_t *in1, uint32_t *in2);
void masked_xor_core(uint32_t *output, uint32_t *in1, uint32_t *in2);
void masked_not_core(uint32_t *output, uint32_t *in);
void masked_and_cst_core(uint32_t *output, uint32_t *in1, uint32_t cst);
void masked_copy_core(uint32_t *output, uint32_t *in);

// Arithmetic utilities
void masked_full_adder(uint32_t *output_s, uint32_t *output_c, uint32_t *in1, uint32_t *in2, uint32_t *in3);
void masked_add_signs(uint32_t *output, uint32_t *in, uint32_t *signs);

// Generic wrapper for Knuth-Yao samplers
// circuit_func: Function pointer to the generated circuit
typedef void (*ky_circuit_func)(uint32_t *output, uint32_t *rs);
void masked_sampler(ky_circuit_func circuit, uint32_t *output, uint32_t *rs, size_t precision);

#endif // GADGETS_MASKED_H