#define TEST
// #define HAWK_256 // Garantit OUTPUT_SIZE = 5


#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include "hal.h"
#include "ky_samplers.h"
#include "gadgets_masked.h"
#include "ky_edge_vectors.h"
#include "bench.h"
#include "masked.h"

#define _W(x) #x
#define W(x) _W(x)
#pragma message "[COMPTIME] NSHARES = " W(NSHARES)
#pragma message "[COMPTIME] NAME = " W(NAME)

#define PRECISION 78
#define RANDOMNESS_MAX_SIZE 79

#if !defined(NUM_BATCHES)
#define NUM_BATCHES 38
#warning "No NUM_BATCHES was providing... going with " W(NUM_BATCHES)
#else
#pragma message "[COMPTIME] NUM_BATCHES = " W(NUM_BATCHES)
#endif


int main(void) {
    hal_setup();
    cyccnt_start();
    hal_send_str("START KNUTH-YAO BENCH");

    uint32_t out[32];

    #if defined(TVLA)
    #pragma message "[COMPTIME] TVLA build"

    trigger_setup();
    uint32_t in[RANDOMNESS_MAX_SIZE]= {1,1,0,1,1,1,1,0,0,0,0,1,1,0,0,1,1,0,0,1,0,1,0,0,1,0,1,0,1,1,1,0,1,0,0,0,0,0,1,1,0,1,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,1,1,0,0,0,0,0,1,1,0,0,0,0,0,0,1,1,0,1,1,0};
    uint32_t masked_input[RANDOMNESS_MAX_SIZE * NSHARES] = {0};
    uint32_t output[OUTPUT_SIZE * NSHARES] = {0};

    for (size_t i = 0; i < RANDOMNESS_MAX_SIZE; i++)
    {
        in[i] = 0 - in[i];
    }
    
    BAIL("Starting infinite sampling...");
    while (1)
    {
        
        char m = getch(); // should wait for input
        // BAIL("got char");

        if (m == 'f') {
            for (size_t i = 0; i < RANDOMNESS_MAX_SIZE; i++)
            {
                mask(masked_input + i * NSHARES, in[i]);
            }
        } else if (m == 'r') {
            for (size_t i = 0; i < RANDOMNESS_MAX_SIZE; i++)
            {
                mask(masked_input + i * NSHARES, get_random());
            }
        } else {
            BAIL("unrecognized mode.");
        }
        /* code */  
        trigger_high();
        masked_sampler(Z(masked_ky_sampler_), output, masked_input, PRECISION);
        trigger_low();
    }
    #else
    #pragma message "[COMPTIME] Bench build"
    #endif

    for(int b = 0; b < NUM_BATCHES; b++) {
        
        
        uint32_t masked_input[RANDOMNESS_MAX_SIZE * NSHARES] = {0};

        for(int bit = 0; bit < RANDOMNESS_MAX_SIZE; bit++) {
            mask(masked_input + bit * NSHARES, get_random());
        }

        #if NSHARES == 1
        uint32_t output[32] = {0};    
        #else
        uint32_t output[OUTPUT_SIZE * NSHARES] = {0};
        #endif
        
        start_bench(sampler);
        #if NSHARES == 1
        transpose32(masked_input); // transpose first 32 inputs
        #endif
        masked_sampler(Z(masked_ky_sampler_), output, masked_input, PRECISION);
        #if NSHARES == 1
        transpose32(output);
        #endif
        stop_bench(sampler);

        // for(int i = 0; i < 32; i++) out[i] = 0;
        // for(int i = 0; i < OUTPUT_SIZE; i++) unmask(out + i, output + i * NSHARES);
        // transpose32(out);

    }
    
    print_all_benches("RESULTS:");
    hal_send_str("EOF");
    while(1);
    return 0;
}