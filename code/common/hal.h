#ifndef HAL_H
#define HAL_H

#ifdef STM32F4
#warning "Compiling HAL for STM32F4"
#include "stm32f4/stm32f4_hal.h"
#endif

#ifdef QEMU
#warning "Compiling HAL for QEMU"
#endif

#include <stdint.h>
#include <stdlib.h>

void hal_setup(void);
void hal_send_str(const char* in);
uint64_t hal_get_time(void);
size_t hal_get_stack_size(void);

#endif
