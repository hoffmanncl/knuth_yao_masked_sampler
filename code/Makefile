PREFIX	?= arm-none-eabi
CC		= $(PREFIX)-gcc
LD		= $(PREFIX)-gcc
AR		= $(PREFIX)-ar
OBJCOPY	= $(PREFIX)-objcopy
OBJDUMP	= $(PREFIX)-objdump
GDB		= $(PREFIX)-gdb

PLATFORM?=QEMU

PARAM?=FRODO_640 # FRODO_640, FRODO_976, FRODO_1344, HAWK_256_T0, etc.
NUM_BATCHES?=200
NSHARES?=2
EXTRAFLAGS?=
CFLAGS += -D$(PARAM) -DNUM_BATCHES=$(NUM_BATCHES) -DNSHARES=$(NSHARES) $(EXTRAFLAGS) -O3

MODE?=test# test, bench, unmasked, ky_unmasked
ifeq ($(MODE),test)
CFLAGS += -DIO_TEST
endif

ifeq ($(MODE),bench)
ifndef BENCH_RND
CFLAGS += -DBENCH_CYC
endif
endif

ifeq ($(MODE),bench_cdt_unmasked)
ifndef BENCH_RND
CFLAGS += -DBENCH_CYC
endif
endif

ifeq ($(MODE),bench_ky_unmasked)
ifndef BENCH_RND
CFLAGS += -DBENCH_CYC
endif
endif

ifeq ($(BENCH),BENCH_RND)
CFLAGS += -DBENCH_RND
endif
ifeq ($(BENCH),BENCH_CYC)
CFLAGS += -DBENCH_CYC
endif

MAIN_SRC = main_$(MODE).c

# =========================================================
# Automatic extraction for scripts (e.g. HAWK_256_T0 -> 256_t0)
# =========================================================
PARAM_LOWER = $(shell echo $(PARAM) | tr 'A-Z' 'a-z')
PARAM_NUM = $(patsubst frodo_%,%,$(patsubst hawk_%,%,$(PARAM_LOWER)))
SAMPLE_FILE = ../scripts/test_$(PARAM_NUM)

# Recompile if a variable changed to prevent stale cache bugs
LAST_BUILD_STATE := $(shell cat .last_build_state 2>/dev/null)
CURRENT_BUILD_STATE := $(PARAM)_$(MODE)_$(NSHARES)_$(PLATFORM)

ifneq ($(LAST_BUILD_STATE),$(CURRENT_BUILD_STATE))
$(info [BUILD] State changed to '$(CURRENT_BUILD_STATE)'. Forcing full clean...)
$(shell echo $(CURRENT_BUILD_STATE) > .last_build_state)
$(shell rm -rf obj/* bin/* elf/* hex/*)
endif

ifeq ($(PLATFORM),QEMU)
LDSCRIPT = obj/ldscript.ld
else ifeq ($(PLATFORM),STM32F3)
LDSCRIPT = common/stm32f3/LinkerScript.ld
else ifeq ($(PLATFORM),STM32F4)
LDSCRIPT = common/stm32f4/LinkerScript.ld
endif

cfiles_base = $(filter-out main%.c, $(wildcard *.c))
cfiles = $(cfiles_base) main_$(MODE).c
hfiles = $(wildcard *.h)
cfiles-o = $(addprefix obj/,$(addsuffix .o,$(cfiles)))

ifeq ($(PLATFORM),QEMU)
# For QEMU target simulation
include qemu.mk

all: bin/$(QEMU-EXEC).bin

else ifeq ($(PLATFORM),STM32F3)

HALPATH = ./common
include ./common/stm32f3/Makefile.stm32f3

make_stm32f3_objs = $(addprefix obj/common/stm32f3/,$(addsuffix .o,$(1)))
src-o = $(call make_stm32f3_objs,$(SRC))
src-o += obj/common/hal-stm32f3.c.o
asrc-o = $(call make_stm32f3_objs,$(ASRC))

LINKDEPS += $(cfiles-o) $(src-o) $(asrc-o) $(LDSCRIPT)
CFLAGS += $(addprefix -I,$(EXTRAINCDIRS))
F_CPU = 7372800
CFLAGS += -Icommon -mcpu=cortex-m4 -DF_CPU=$(F_CPU) -DSS_VER=NONE
LDFLAGS += -Lobj

all: hex/stm.hex

else ifeq ($(PLATFORM),STM32F4)

HALPATH = ./common
include ./common/stm32f4/Makefile.stm32f4

make_stm32f4_objs = $(addprefix obj/common/stm32f4/,$(addsuffix .o,$(1)))
src-o = $(call make_stm32f4_objs,$(SRC))
src-o += obj/common/hal-stm32f4.c.o 
asrc-o = $(call make_stm32f4_objs,$(ASRC))
# asrc-o += obj/transpose.S.o

LINKDEPS += $(cfiles-o) $(src-o) $(asrc-o) $(LDSCRIPT)
CFLAGS += $(addprefix -I,$(EXTRAINCDIRS))
CFLAGS += -Icommon -mcpu=cortex-m4 -DSS_VER=1 $(CDEFS)
LDFLAGS += -Lobj

all: hex/stm.hex elf/stm.elf

endif

run-bench:
	@python3 ../scripts/bench.py run

# =========================================================
# QEMU Run Target with stdout parsing and sample routing
# =========================================================
run-test: bin/$(QEMU-EXEC).bin
	@mkdir -p ../scripts
	@rm -f $(SAMPLE_FILE)
	@echo "\nRunning QEMU simulation..."
	@echo "Intercepting samples and routing to: $(SAMPLE_FILE)\n"
	@qemu-system-arm -M mps2-an386 -nographic -semihosting -kernel bin/$(QEMU-EXEC).bin | awk '\
		/^\[SAMPLE\]/ { print $$2 >> "$(SAMPLE_FILE)"; next } \
		/^EOF/ { print "\n[INFO] End of execution reached. QEMU terminated."; exit } \
		{ print }'

hex/%.hex: elf/%.elf
	$(Q)[ -d $(@D) ] || mkdir -p $(@D)
	$(OBJCOPY) -O ihex -R .eeprom -R .fuse -R .lock -R .signature $< $@

obj/_ELFNAME_%.o: $(LINKDEPS)
	@echo "  GEN      $@"
	$(Q)echo "const char _elf_name[] = \"$(ELFNAME)\";" | \
		$(CC) -x c -c -o $@ $(filter-out -g3,$(CFLAGS)) -

elf/%.elf:  obj/_ELFNAME_%.elf.o $(LINKDEPS)
	@echo "  LD       $@"
	$(Q)[ -d $(@D) ] || mkdir -p $(@D)
	$(Q)$(LD) $(CFLAGS) $(LDFLAGS) -o $@ $(filter %.o,$^) -Wl,--start-group $(LDLIBS) -Wl,--end-group

bin/%.bin: elf/%.elf
	@echo "  OBJCOPY  $@"
	$(Q)[ -d $(@D) ] || mkdir -p $(@D)
	$(Q)$(OBJCOPY) -Obinary $< $@

# General compilation rules

obj/%.c.o : %.c
	$(Q)[ -d $(@D) ] || mkdir -p $(@D)
	$(CC) -c -o $@ $(CFLAGS) $<

obj/%.S.o : %.S
	$(Q)[ -d $(@D) ] || mkdir -p $(@D)
	$(CC) -c -o $@ $(CFLAGS) $<

obj/%.a:
	$(Q)[ -d $(@D) ] || mkdir -p $(@D)
	$(Q)$(AR) rcs $@ $(filter %.o,$^)

clean:
	find . -name \*.o -type f -exec rm -f {} \;
	find . -name \*.d -type f -exec rm -f {} \;
	rm -rf obj/* bin/* elf/* hex/*