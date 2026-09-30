#define TEST
/**
 * @file main_unmasked_bench.c
 * @brief Unmasked Packed KY Benchmark.
 */

#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include "hal.h"
#include "unmasked_ky_samplers.h"
#include "bench.h"

// Define parameter specifics based on compilation macros
#if defined(FRODO_640)
    #define PARAM_NAME "unmasked_ky_frodo_640"
    #define INPUT_SIZE 16
    #define OUTPUT_SIZE 5
    #define Z_SAMPLER unmasked_ky_sampler_frodo640
#elif defined(FRODO_976)
    #define PARAM_NAME "unmasked_ky_frodo_976"
    #define INPUT_SIZE 16
    #define OUTPUT_SIZE 5
    #define Z_SAMPLER unmasked_ky_sampler_frodo976
#elif defined(FRODO_1344)
    #define PARAM_NAME "unmasked_ky_frodo_1344"
    #define INPUT_SIZE 16
    #define OUTPUT_SIZE 4
    #define Z_SAMPLER unmasked_ky_sampler_frodo1344
#else
    #error "Please define a parameter set (e.g., FRODO_1344)"
#endif

// --- Packing Configuration ---
#define PACK_OUT (32 / OUTPUT_SIZE)
#define PACK_IN  (32 / INPUT_SIZE)

// Pre-calculate number of 32x32 input matrices needed for a full output batch
#define NUM_IN_MATRICES ((PACK_OUT + PACK_IN - 1) / PACK_IN)

#ifndef NUM_BATCHES
#define NUM_BATCHES 1000
#endif

// Expected external helper
extern void transpose32(uint32_t a[32]);
extern uint32_t get_random(void);

int main(void) {
    hal_setup();
    reset_benches();
    
    // volatile to avoid optimization removal
    volatile uint32_t sink = 0;

    for (int batch = 0; batch < NUM_BATCHES; batch++) {
        uint32_t out_matrix[32] = {0};
        
        // 1. Input randomness generation out of the bench 
        uint32_t random_inputs[NUM_IN_MATRICES][32];
        for (int m = 0; m < NUM_IN_MATRICES; m++) {
            for (int i = 0; i < 32; i++) {
                random_inputs[m][i] = get_random();
            }
        }

        uint32_t transposed_inputs[NUM_IN_MATRICES][32];

        // 2. Input Transposition phase
        #ifdef BENCH_INPUT
        start_bench(sampler);
        #endif

        for (int m = 0; m < NUM_IN_MATRICES; m++) {
            for (int i = 0; i < 32; i++) {
                transposed_inputs[m][i] = random_inputs[m][i];
            }
            transpose32(transposed_inputs[m]);
        }

        #ifndef BENCH_INPUT
        start_bench(sampler);
        #endif

        // 3. Execution of packed runs
        for (int r = 0; r < PACK_OUT; r++) {
            uint32_t run_output[OUTPUT_SIZE] = {0};
            
            // FRODO Case: 16-bit precision, packed 2 per register
            int m = r / PACK_IN;
            int offset = (r % PACK_IN) * INPUT_SIZE;
            Z_SAMPLER(run_output, transposed_inputs[m] + offset);

            // Pack the magnitude out of the circuit into the output matrix.
            // OUTPUT_SIZE implies +1 for the sign bit (skipped here as KY generates only magnitude)
            for (int b = 0; b < OUTPUT_SIZE - 1; b++) {
                out_matrix[r * OUTPUT_SIZE + b] = run_output[b];
            }
            sink ^= run_output[0];
        }

        // 4. Output Transposition phase (Always timed as part of the core operation)
        transpose32(out_matrix);
        stop_bench(sampler);
        
        sink ^= out_matrix[0];
    }

    (void)sink;
    print_all_benches(PARAM_NAME);
    hal_send_str("EOF");

    while(1);
    return 0;
}