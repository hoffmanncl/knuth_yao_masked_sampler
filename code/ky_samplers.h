#ifndef KY_SAMPLERS_H
#define KY_SAMPLERS_H

#include "gadgets_masked.h"

void masked_ky_sampler_frodo640(uint32_t *output, uint32_t *rs);
void masked_ky_sampler_frodo976(uint32_t *output, uint32_t *rs);
void masked_ky_sampler_frodo1344(uint32_t *output, uint32_t *rs);
void masked_ky_sampler_hawk256_t0(uint32_t *output, uint32_t *rs);
void masked_ky_sampler_hawk256_t1(uint32_t *output, uint32_t *rs);
void masked_ky_sampler_hawk512_t0(uint32_t *output, uint32_t *rs);
void masked_ky_sampler_hawk512_t1(uint32_t *output, uint32_t *rs);
void masked_ky_sampler_hawk1024_t0(uint32_t *output, uint32_t *rs);
void masked_ky_sampler_hawk1024_t1(uint32_t *output, uint32_t *rs);
void masked_ky_sampler_falcon_base(uint32_t *output, uint32_t *rs);
void masked_ky_sampler_haetae_base(uint32_t *output, uint32_t *rs);

#endif // KY_SAMPLERS_H
