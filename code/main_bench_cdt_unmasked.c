/*
 * Constant-Time Scalar CDT Benchmark
 * Compiles alongside the pqm4 benchmarking environment.
 */

#include <stdint.h>
#include <stddef.h>
#include "bench.h"
#include "hal.h"
#include "out_gadgets_masked.h"
#include "scalar_cdt_tables.h"

#define _W(x) #x
#define W(x) _W(x)

#define NUM_BATCHES 10000

#if defined(FRODO_640)
    #define PARAM_NAME "scalar_frodo_640"
    #define IS_HAWK 0
    #define TABLE FRODO640_CDT_TABLE
    #define T_SIZE FRODO640_CDT_SIZE
#elif defined(FRODO_976)
    #define PARAM_NAME "scalar_frodo_976"
    #define IS_HAWK 0
    #define TABLE FRODO976_CDT_TABLE
    #define T_SIZE FRODO976_CDT_SIZE
#elif defined(FRODO_1344)
    #define PARAM_NAME "scalar_frodo_1344"
    #define IS_HAWK 0
    #define TABLE FRODO1344_CDT_TABLE
    #define T_SIZE FRODO1344_CDT_SIZE
#elif defined(HAWK_256_T0)
    #define PARAM_NAME "scalar_hawk_256_t0"
    #define IS_HAWK 1
    #define TABLE HAWK256_T0_CDT_TABLE
    #define T_SIZE HAWK256_T0_CDT_SIZE
#elif defined(HAWK_256_T1)
    #define PARAM_NAME "scalar_hawk_256_t1"
    #define IS_HAWK 1
    #define TABLE HAWK256_T1_CDT_TABLE
    #define T_SIZE HAWK256_T1_CDT_SIZE
#elif defined(HAWK_512_T0)
    #define PARAM_NAME "scalar_hawk_512_t0"
    #define IS_HAWK 1
    #define TABLE HAWK512_T0_CDT_TABLE
    #define T_SIZE HAWK512_T0_CDT_SIZE
#elif defined(HAWK_512_T1)
    #define PARAM_NAME "scalar_hawk_512_t1"
    #define IS_HAWK 1
    #define TABLE HAWK512_T1_CDT_TABLE
    #define T_SIZE HAWK512_T1_CDT_SIZE
#elif defined(HAWK_1024_T0)
    #define PARAM_NAME "scalar_hawk_1024_t0"
    #define IS_HAWK 1
    #define TABLE HAWK1024_T0_CDT_TABLE
    #define T_SIZE HAWK1024_T0_CDT_SIZE
#elif defined(HAWK_1024_T1)
    #define PARAM_NAME "scalar_hawk_1024_t1"
    #define IS_HAWK 1
    #define TABLE HAWK1024_T1_CDT_TABLE
    #define T_SIZE HAWK1024_T1_CDT_SIZE
#else
    #error "Please define a parameter set (e.g., FRODO_640 or HAWK_256_T0)"
#endif

#pragma message "[COMPTIME] NSHARES = " W(NSHARES)
#pragma message "[COMPTIME] NAME = " W(NAME)
#pragma message "[COMPTIME] PARAM_NAME = " W(PARAM_NAME)

// ========================================================================
// Constant-Time Primitives
// ========================================================================

// Constant-time sign application: returns -sample if sign_bit == 1, else sample
static inline int32_t ct_apply_sign(uint32_t sample, uint32_t sign_bit) {
    int32_t mask = -(int32_t)sign_bit;
    return (sample ^ mask) - mask;
}

#if IS_HAWK
// Constant-time 3x32-bit comparison (x < y).
// Uses borrow-out logic from multi-precision subtraction.
static inline uint32_t ct_lt_3x32(const uint32_t x[3], const uint32_t y[3]) {
    uint64_t diff0 = (uint64_t)x[0] - y[0];
    uint64_t diff1 = (uint64_t)x[1] - y[1] - (diff0 >> 63);
    uint64_t diff2 = (uint64_t)x[2] - y[2] - (diff1 >> 63);
    return (uint32_t)((diff2 >> 63) & 1);
}

// Hawk Sampler: Uses RCDT natively (prnd < RCDT[i])
static int32_t sample_cdt_scalar(const uint32_t rnd_words[3], uint32_t sign_bit) {
    uint32_t sample = 0;
    for (size_t i = 0; i < T_SIZE; ++i) {
        sample += ct_lt_3x32(rnd_words, TABLE[i]);
    }
    return ct_apply_sign(sample, sign_bit);
}
#else
// Frodo Sampler: Uses CDF natively (prnd > CDF[i])
static int32_t sample_cdt_scalar(uint16_t rand_in) {
    uint16_t prnd = rand_in >> 1;
    uint32_t sign_bit = rand_in & 1;
    uint32_t sample = 0;
    for (size_t i = 0; i < T_SIZE; ++i) {
        // Compiler typically translates this boolean directly to a branchless add
        sample += (prnd > TABLE[i]); 
    }
    return ct_apply_sign(sample, sign_bit);
}
#endif

// ========================================================================
// Main Execution
// ========================================================================
int main(void) {
    hal_setup();

    volatile int32_t res;
    
    // Memory structures for randomness depending on the scheme
    #if IS_HAWK
        uint32_t rnd[3];
        uint32_t rnd_sign;
    #else
        uint32_t rnd_frodo;
    #endif

    // Warmup phase
    #if IS_HAWK
        for (size_t i = 0; i < 3; i++)
        {
            rnd[i] = get_random();
        }

        rnd_sign = get_random();
        
        res = sample_cdt_scalar(rnd, rnd_sign & 1);
    #else
        rnd_frodo = get_random();
        res = sample_cdt_scalar(rnd_frodo);
    #endif
    (void)res;

    reset_benches();

    // Benchmarking loop
    for (int i = 0; i < NUM_BATCHES; i++) {
        // Fetch randomness OUTSIDE the bench macro to measure only arithmetic
        #if IS_HAWK
            for (size_t i = 0; i < 3; i++)
            {
                rnd[i] = get_random();
            }

            rnd_sign = get_random();
            
            res = sample_cdt_scalar(rnd, rnd_sign & 1);
            
            start_bench(sampler);
            res = sample_cdt_scalar(rnd, rnd_sign & 1);
            stop_bench(sampler);
        #else
            rnd_frodo = get_random();
            
            start_bench(sampler);
            res = sample_cdt_scalar(rnd_frodo);
            stop_bench(sampler);
        #endif
    }

    // Export the benchmark times for your CSV framework
    print_all_benches(PARAM_NAME);
    BAIL("EOF");
    
    while(1);
    return 0;
}