QEMU-EXEC=qemu
MPS2_DATA_IN_FLASH = 1 # see what that does exactly, necessary for the .S compilation
ARCH_FLAGS += -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16

 # --specs=nosys.specs needed for LDFLAGS but if used twice generates error
CFLAGS += \
	$(ARCH_FLAGS) \
	--specs=nosys.specs \
	-Icommon -Icommon/mps2\
	$(OPT)

LDFLAGS += \
	-Wl,--wrap=_sbrk \
	-ffreestanding \
	-Lobj \
	-T$(LDSCRIPT) \
	$(ARCH_FLAGS)

CPPFLAGS += \
	-DMPS2_AN386

QEMU_LIBHAL_SRC := \
	common/mps2/startup_MPS2.S \
	common/hal-mps2.c \
	common/randombytes.c

qemu_lhal_objs = $(addprefix obj/,$(addsuffix .o,$(1)))
obj/libpqm4hal.a: $(call qemu_lhal_objs,$(QEMU_LIBHAL_SRC))
obj/libpqm4hal.a: CPPFLAGS += -Icommon/mps2
$(LDSCRIPT): CPPFLAGS += $(if $(MPS2_DATA_IN_FLASH),-DDATA_IN_FLASH)
obj/common/mps2/startup_MPS2.S.o: CFLAGS += -DDATA_IN_FLASH

LDLIBS += -lpqm4hal$(if $(NO_RANDOMBYTES),-nornd)
LIBDEPS += obj/libpqm4hal.a

$(LDSCRIPT): common/mps2/MPS2.ld
	$(Q)[ -d $(@D) ] || mkdir -p $(@D)
	$(CC) -x assembler-with-cpp -E -Wp,-P $(CPPFLAGS) $< -o $@

$(LDSCRIPT): CPPFLAGS += -Icommon/mps2

LINKDEPS += $(LDSCRIPT) $(LIBDEPS) $(cfiles-o)