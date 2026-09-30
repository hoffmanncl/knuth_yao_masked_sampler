#include "out_gadgets_masked.h"
#include "hal.h"
#if defined(STM32F3) || defined(STM32F4)
// #include "randombytes.h"
#warning "COMPILING STM32F VERSION, USING HARDWARE RANDOMNESS"
// uint32_t get_random() {

// #if BENCH_RND == 1
//   rng_cnt += 1;
// #endif
//   while (1) {
//     if ((RNG_SR & RNG_SR_DRDY) == 1) { // check if data is ready
//       return RNG_DR;
//     }
//   }
//   return 0;
// }
inline uint32_t get_random() {
  #if defined(BENCH_RND)
  extern uint64_t rng_cnt;
  rng_cnt += 1;
  #endif
  return get_rand();
}

#else
#warning "COMPILING QEMU VERSION, NO HARDWARE RANDOMNESS"
uint32_t get_random() {
    // A remplacer par un TRNG. Utiliser une astuce pour ne jamais perdre de bit de RNG
    return (uint32_t)rand() ^ ((uint32_t)rand() << 16); 
}
#endif

// code from CS20
static inline uint32_t pini_and_core(uint32_t a, uint32_t b, uint32_t r) {
  uint32_t temp;
  uint32_t s;
  asm("eor %[temp], %[b], %[r]\n\t"
      "and %[temp], %[a], %[temp]\n\t"
      "bic %[s], %[r], %[a]\n\t"
      "eor %[s], %[s], %[temp]"
      : [s] "=r"(s), [temp] "=&r"(temp)    /* outputs, use temp as an
                                              arbitrary-location clobber */
      : [a] "r"(a), [b] "r"(b), [r] "r"(r) /* inputs */
  );
  return s;
}

void masked_xor_c(size_t nshares, uint32_t *out, size_t out_stride,
                  const uint32_t *ina, size_t ina_stride, const uint32_t *inb,
                  size_t inb_stride) {
  for (size_t i = 0; i < nshares; i++) {
    out[i * out_stride] = ina[i * ina_stride] ^ inb[i * inb_stride];
  }
}

void masked_and_c(size_t nshares, uint32_t *z, size_t z_stride,
                  const uint32_t *a, size_t a_stride, const uint32_t *b,
                  size_t b_stride) {
  uint32_t ztmp[nshares];
  uint32_t r;
  uint32_t i, j;

  for (i = 0; i < nshares; i++) {
    ztmp[i] = a[i * a_stride] & b[i * b_stride];
  }

  for (i = 0; i < (nshares - 1); i++) {
    for (j = i + 1; j < nshares; j++) {
      r = get_random();
      // PINI
      ztmp[i] ^= pini_and_core(a[i * a_stride], b[j * b_stride], r);
      ztmp[j] ^= pini_and_core(a[j * a_stride], b[i * b_stride], r);
    }
  }
  for (i = 0; i < nshares; i++) {
    z[i * z_stride] = ztmp[i];
  }
}
