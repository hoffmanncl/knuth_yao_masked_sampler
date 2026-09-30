#ifndef MASKED_H
#define MASKED_H


#if defined(FRODO_1344)
#define NAME frodo1344
#elif defined(FRODO_976)
#define NAME frodo976
#elif defined(FRODO_640)
#define NAME frodo640
#elif defined(HAWK_256_T0)
#define NAME hawk256_t0
#elif defined(HAWK_256_T1)
#define NAME hawk256_t1
#elif defined(HAWK_512_T0)
#define NAME hawk512_t0
#elif defined(HAWK_512_T1)
#define NAME hawk512_t1
#elif defined(HAWK_1024_T0)
#define NAME hawk1024_t0
#elif defined(HAWK_1024_T1)
#define NAME hawk1024_t1
#elif defined(HAETAE)
#define NAME haetae_base
#define NOADDSIGNS // remove add_signs from benches
#elif defined(FALCON)
#define NAME falcon_base
#define NOADDSIGNS // remove add_signs from benches
#else
#define NAME UNKNOWN
#endif

#define _Z(A, B) A ## B
#define EXPAND_Z(A, B) _Z(A, B)
#define Z(A) EXPAND_Z(A, NAME)

#if !defined(NSHARES)
#warning "Using default NSHARES=2"
#define NSHARES 2
#endif
#define WORDSIZE 32


// #if !defined(FRODO_640) && !defined(FRODO_976) && !defined(FRODO_1344) && \
//     !defined(HAWK_256_T0) && !defined(HAWK_512_T0) && !defined(HAWK_1024_T0) && \
//     !defined(HAWK_256_T1) && !defined(HAWK_512_T1) && !defined(HAWK_1024_T1) 
//     #define FRODO_640
// #endif

#if defined(FRODO_1344)
    #define OUTPUT_SIZE 4
#elif defined(HAWK_256_T0) || defined(HAWK_256_T1) ||\
    defined(HAWK_512_T0) || defined(HAWK_512_T1) || \
    defined(HAWK_1024_T0) || defined(HAWK_1024_T1) || \
    defined(FRODO_640) || defined(FRODO_976)
    #define OUTPUT_SIZE 5
#else
    #define OUTPUT_SIZE 8
#endif

#endif
