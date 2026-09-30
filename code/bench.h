/* Copyright 2022 UCLouvain, Belgium and PQM4 contributors
 *
 * This file is part of pqm4_masked.
 *
 * pqm4_masked is free software: you can redistribute it and/or modify it under
 * the terms of the GNU General Public License as published by the Free
 * Software Foundation, version 3.
 *
 * pqm4_masked is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along with
 * pqm4_masked. If not, see <https://www.gnu.org/licenses/>.
 */

#ifndef BENCH_H
#define BENCH_H

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include "hal.h"
#include "sendfn.h"
#include "masked.h"

// #if !defined(NSHARES)
// #define NSHARES 1 // needed for bench
// #endif

#define BENCH_CASES X(sampler)

#if defined(BENCH_CYC) || defined(BENCH_RND)
#define BENCHING
#endif


typedef enum {
#define X(x) x,
BENCH_CASES
#undef X
} bench_case;

void reset_bench(bench_case bench);
void reset_benches();
void start_bench(bench_case bench);
void stop_bench(bench_case bench);
uint32_t bench_tot_time(bench_case bench);
uint32_t bench_tot_calls(bench_case bench);
void cyccnt_start();
void print_bench(bench_case bench, const char *s);
void print_all_benches(const char *s);

#endif // BENCH_H
