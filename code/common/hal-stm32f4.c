// custom hal part of stm32f4_hal.c
#include "hal.h"
#include "stm32f4/stm32f4_hal.h"

void hal_setup() {
    platform_init();
    init_uart();
}

void hal_send_str(const char* in)
{
  const char* cur = in;
  while (*cur) {
    putch(*cur);
    cur += 1;
  }
  putch('\n');
}

uint64_t hal_get_time(void) {
    return 1;
}

extern char end;
static char* heap_end = &end;

size_t hal_get_stack_size(void) {
    register char* cur_stack;
	__asm__ volatile ("mov %0, sp" : "=r" (cur_stack));
    return cur_stack - heap_end;
}