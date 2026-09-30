#ifndef UNMASKED_KY_SAMPLERS_H
#define UNMASKED_KY_SAMPLERS_H

#include <stdint.h>

void unmasked_ky_sampler_kyber768_eta2(uint32_t *output, uint32_t *rs);
void unmasked_ky_sampler_frodo640(uint32_t *output, uint32_t *rs);
void unmasked_ky_sampler_frodo976(uint32_t *output, uint32_t *rs);
void unmasked_ky_sampler_frodo1344(uint32_t *output, uint32_t *rs);
void unmasked_ky_sampler_hawk256_t0(uint32_t *output, uint32_t *rs);
void unmasked_ky_sampler_hawk256_t1(uint32_t *output, uint32_t *rs);
void unmasked_ky_sampler_hawk512_t0(uint32_t *output, uint32_t *rs);
void unmasked_ky_sampler_hawk512_t1(uint32_t *output, uint32_t *rs);
void unmasked_ky_sampler_hawk1024_t0(uint32_t *output, uint32_t *rs);
void unmasked_ky_sampler_hawk1024_t1(uint32_t *output, uint32_t *rs);

#endif // UNMASKED_KY_SAMPLERS_H
