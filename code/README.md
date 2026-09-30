# Masked Knuth-Yao Sampler

This repository contains the source code for the masked bitsliced implementation of the FrodoKEM and HAWK KY-based Gaussian sampler. It provides an exhaustive functional correctness test suite, a performance benchmarking framework, and the tooling used to generate the underlying Boolean logic.

## Repository Structure

To facilitate artifact evaluation, the cryptographic implementations and tools are clearly separated:

* **`gadgets_masked.c` & `gadgets_masked.h`**: Contains our novel contributions, including the bitsliced sampler for every FrodoKEM parameter sets.
* **`out_gadgets_masked.c`**: Contains standard masked gadgets and foundational functions derived from other projects (primarily from `pqm4_masked`).
* **`main_test.c`**: Main for the exhaustive Known Answer Tests (KAT) and distribution collection.
* **`main_bench.c`**: Main for performance evaluation (cycle counts and randomness consumption).
* **`main_bench_cdt_unmasked.c`** and **`main_bench_ky_unmasked.c`**: Main for performance evaluation of the unmasked samplers, used in Section 6 (cycle counts).
* **Python Scripts**: We also join the Python scripts used to generate the masked circuits required by the sampler (**`generate_circuit.py`**, which comes with instructions to add extra distributions if needed),  to generate the unmasked KY circuit for `main_bench_ky_unmasked.c`(**`unmask_ky.py`**) for main, to generate the CDTs for `main_bench_cdt_unmasked.c` (**generate_cdt.py**), and run the benchmarks (**`bench.py`**).

## Prerequisites

To compile and run this project, you will need the standard ARM bare-metal
toolchain, QEMU for emulation, and Python:
* `arm-none-eabi-gcc` (Toolchain)
* `qemu-system-arm` (For local emulation)
* `make`
* `python3` (For the bitsliced table generation script and plotting
distributions)

The python libraries used are:
* `chipwhisperer` used for all communications with the target
* `matplotlib` used to plot output distributions

To install all the python dependencies used by the script,
please create a new python virtual environment and run
```bash
pip install -r requirements.txt
```

## Build and Run Instructions

The build system is entirely driven by `make`. You can configure the target
platform, the FrodoKEM parameter set, and the execution mode using environment
variables.

### General Command Syntax

To run tests to check that the output distribution is correct (runs on QEMU)
use:

```bash
make run-test <NSHARES> <PARAM>
```
The test checks the exactness of our masked gadget (for the parameter set
`<PARAM>` with masking using `<NSHARES>` shares) by running it against all
65,536 possible 16-bit algorithmic randomness inputs and compares the results
against the unmasked FrodoKEM specification. A successful run guarantees 100%
equivalent distributions. Then the standard output is parsed and routes the raw
integer samples into a dedicated file (e.g., `../scripts/test_640`), ready to be
plotted by our Python script `scripts/distributions.py`. To show the
distribution curve, simply run `python3 scripts/distributions.py <paramset>`,
where `<paramset>` is the selected parameter set (i.e. 640, 976 or 1344). For
how to set the parameters `<PARAM>` and `<NSHARES>`, see Section *Configuration
Variables*.


To reproduce the benchmarks results of the paper (on a STM32F3 or STM32F4 via a
Chipwhisperer) use:

```bash
make run-bench
```
This generates automatically the .hex files for all parameter sets and number of
shares from 2 to 6, uploads them one by one to the target and reads the output
(via the UART protocol) to get the results. Results are collected and written in
a file called `bench-results-2shares-to-9shares.txt` in the `code` folder. Note
that our benchmarks are done on the STM32F4 since it has a TRNG.


To build a .hex file of the `main_<MODE>.c` program run
```bash
make PLATFORM=<PLATFORM> PARAM=<PARAM> MODE=<MODE> NSHARES=<NSHARES> NUM_BATCHES=<NUM_BATCHES> BENCH=<BENCH_TYPE>
```

### Configuration Variables

#### 1. `PLATFORM`
* **`QEMU`**: (Default) Compiles the code to run on the QEMU emulator. Ideal for verifying functional correctness locally without hardware.
* **`STM32F3`**: Compiles for the STM32F303 board. Required for accurate cycle counts and performance benchmarking.

#### 2. `PARAM` (FrodoKEM Parameter Set)
* **`FRODO_1344`**
* **`FRODO_976`**
* **`FRODO_640`** (Default)
* **`HAWK_256_T0`**
* **`HAWK_256_T1`**
* **`HAWK_512_T0`**
* **`HAWK_512_T1`**
* **`HAWK_1024_T0`**
* **`HAWK_1024_T1`**

#### 3. `MODE` (Execution Mode)
* **`test`**: compiles the file `main_test.c`, file used for tests.
* **`bench`**: compiles the file `main_bench.c`, file used for benchmarks.
* **`bench_ky_unmasked`**: compiles the file `main_bench_ky_unmasked.c`, file used for benchmarks.
* **`bench_cdt_unmasked`**: compiles the file `main_bench_cdt_unmasked.c`, file used for benchmarks.
    
    ⚠️ While `MODE=bench` can be compiled and executed using `PLATFORM=QEMU`, QEMU is *not* a cycle-accurate emulator. Timing results obtained in QEMU are meaningless. To reproduce the performance tables from the paper, you must compile with `PLATFORM=STM32F3` or `PLATFORM=STM32F4` and run the binary on a real micro-controller.
    
    ⚠️ Since the STM32F3 does not have a TRNG, randomness calls for this platform are calls to the `rand` function. On a STM32F4, we actually use the TRNG of the target.


#### 4. `NSHARES` (Number of shares for masking)
Default value is 2, but can be any non-zero integer.

#### 5. `NUM_BATCHES` (Number loop iteration for benchmarks)
This variable defines the number of calls to the sampler for the benchmarks. Default value is 200. If `MODE=test`, it has no effect.

#### 6. `BENCH` (Benchmark cycles or randomness)
* **`BENCH_CYC`**: (Default) Count the number of cycles
* **`BENCH_RNG`**: (Default) Count the number of calls to `get_random` function (outputs 32 bits of randomness)
If `MODE=test`, it has no effect.


## Benchmarking

For simplicity, we relied on the Chipwhisperer to communicate with the target.
We therefore implemented the benchmarks using it, which makes the chipwhisperer
library necessary
[(installation-guide)](https://chipwhisperer.readthedocs.io/en/latest/installation.html).

*Note: The following benchmarking instructions are derived from the [pqm4_masked
repository](https://github.com/simple-crypto/pqm4_masked?tab=readme-ov-file) as
we copied their benchmarking process.*

We provide a profiling framework that measures the execution time of sub-parts
of the implementations. To configure the measured parts, first edit
`BENCH_CASES` in `common/bench.h` (we provide a reasonable default).

Example (to measure `my_function` and `my_other_function`):

```c
#define BENCH_CASES X(my_function) X(my_other_function)
```

Then you increase the performance counter of that part where it is called:

```c
start_bench(my_function);
my_function(...); // This can be any block of code you want to measure.
stop_bench(my_function);
```

See also `common/bench.c` and `common/speed_sub.c` for additional details about the profiling framework.
