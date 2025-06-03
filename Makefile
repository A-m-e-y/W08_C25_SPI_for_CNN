# Makefile for running Cocotb test with Icarus Verilog

TOPLEVEL_LANG = verilog
TOPLEVEL = device_b
MODULE = test_device_a

VERILOG_SOURCES = $(shell pwd)/RTL/device_b.v $(shell pwd)/RTL/spi_slave.v

SIM = icarus
WAVES = 1

# Cocotb build system
include $(shell cocotb-config --makefiles)/Makefile.sim
