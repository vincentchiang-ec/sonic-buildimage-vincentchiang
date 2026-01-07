ifneq ($(KERNELRELEASE),)
obj-m:= x86-64-accton-as7327-56x-cpld.o x86-64-accton-as7327-56x-fpga.o \
	x86-64-accton-as7327-56x-leds.o x86-64-accton-as7327-56x-psu.o \
	at24_as7327_56x.o

ifeq (,$(KERNEL_SRC))
$(error KERNEL_SRC is not defined)
else
KERNELDIR:=$(KERNEL_SRC)
endif
PWD:=$(shell pwd)
default:
	$(MAKE) -C $(KERNELDIR)  M=$(PWD) modules
clean:
	rm -rf *.o *.mod.o *.mod.o *.ko .*cmd .tmp_versions Module.markers Module.symvers modules.order
endif
