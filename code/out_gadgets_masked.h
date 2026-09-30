#include <stdint.h>
#include <stdlib.h>

#define BAIL(...)                                                              \
  do {                                                                         \
    char bail_buf[100];                                                        \
    sprintf(bail_buf, __VA_ARGS__);                                            \
    hal_send_str(bail_buf);                                                    \
  } while (0);
  
uint32_t get_random(); // TODO: TRNG

static inline uint32_t pini_and_core(uint32_t a, uint32_t b, uint32_t r);
void masked_xor_c(size_t nshares, uint32_t *out, size_t out_stride,
                  const uint32_t *ina, size_t ina_stride, const uint32_t *inb,
                  size_t inb_stride);
void masked_and_c(size_t nshares, uint32_t *z, size_t z_stride,
                  const uint32_t *a, size_t a_stride, const uint32_t *b,
                  size_t b_stride);