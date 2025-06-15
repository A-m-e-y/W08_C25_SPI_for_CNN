# W08_C25_SPI_for_CNN

Course: HW for AI & ML, Week 8 Challenge 25  
Designing a bi-directional SPI channel for sending and receiving data to a MatrixMulEngine designed in a CNN project.

---

## Table of Contents

- [Project Overview](#project-overview)
- [System Architecture](#system-architecture)
- [File-by-File Breakdown](#file-by-file-breakdown)
  - [RTL/ (Verilog Hardware)](#rtl-verilog-hardware)
  - [Python Testbench and Interface](#python-testbench-and-interface)
  - [Simulation and Build Artifacts](#simulation-and-build-artifacts)
  - [Other Files](#other-files)
- [Detailed Data Flow](#detailed-data-flow)
- [How to Run the Project](#how-to-run-the-project)
- [Results](#results)
- [How everything connects](#how-everything-connects)

---

## Project Overview

This project implements and verifies a bi-directional SPI (Serial Peripheral Interface) communication channel between two devices, `device_a` (master) and `device_b` (slave), in Verilog. The system is designed to send a 32-bit value from `device_a` to `device_b`, have `device_b` increment the value, and then return it to `device_a` via SPI. The project includes:

- Modular Verilog RTL for both master and slave SPI logic.
- A Python-based cocotb testbench for automated simulation and verification.
- A Python hardware interface for stress-testing the SPI channel with random floating-point values.
- A Makefile-based simulation flow using Icarus Verilog and cocotb.

---

## System Architecture

```
+-------------------+      SPI      +-------------------+
|    device_a.v     |<------------->|    device_b.v     |
|   (SPI Master)    |               |   (SPI Slave)     |
+-------------------+               +-------------------+
        ^                                  ^
        |                                  |
        |                                  |
        |                                  |
        |                                  |
+-------------------+               +-------------------+
|   Python/Cocotb   |               |   spi_slave.v     |
|   test_device_a.py|               |   (RTL)           |
+-------------------+               +-------------------+
        ^                                  ^
        |                                  |
        +----------+   Makefile   +---------+
                   |              |
                   v              v
             hw_spi_interface.py  test_tx_rx_spi.py
```

- **device_a.v**: SPI master, initiates communication, sends data, receives response.
- **device_b.v**: SPI slave, receives data, increments it, sends response.
- **spi_master.v / spi_slave.v**: Core SPI protocol logic.
- **spi_top.v**: Top-level module connecting master and slave.
- **tb_spi_top.v**: Verilog testbench for waveform-based simulation.
- **test_device_a.py**: Python cocotb testbench, behavioral model of device_a FSM.
- **hw_spi_interface.py**: Python interface to run hardware simulation and extract results.
- **test_tx_rx_spi.py**: Python script for stress-testing the SPI channel with random floats.
- **Makefile**: Simulation build and run automation.

---

## File-by-File Breakdown

### RTL/ (Verilog Hardware)

#### [`RTL/device_a.v`](RTL/device_a.v)
Implements the SPI master device (`device_a`).  
- **Inputs**: `clk`, `rst_n`, `in_data` (data to send), `response_ready`, `miso`
- **Outputs**: `sclk`, `mosi`, `cs_n`, `out_data` (received response), `done_B_to_A`
- **FSM**: Controls the SPI master protocol, manages two phases:
  1. Sends `in_data` to slave.
  2. Waits for `response_ready`, then initiates a dummy transfer to receive the incremented value.
- **Uses**: Instantiates [`spi_master`](RTL/spi_master.v).

#### [`RTL/device_b.v`](RTL/device_b.v)
Implements the SPI slave device (`device_b`).  
- **Inputs**: `clk`, `rst_n`, `sclk`, `cs_n`, `mosi`
- **Outputs**: `miso`, `out_data` (received data), `response_ready`
- **Role**: Instantiates [`spi_slave`](RTL/spi_slave.v), latches received data, and exposes it on `out_data` when valid.

#### [`RTL/spi_master.v`](RTL/spi_master.v)
Implements the SPI master protocol logic.  
- **Inputs**: `clk`, `rst_n`, `start`, `hold_cs`, `data_in`
- **Outputs**: `sclk`, `mosi`, `cs_n`, `busy`
- **FSM**: Handles SPI transaction, toggles `sclk`, shifts out `mosi`, manages `cs_n` assertion/deassertion, and busy status.

#### [`RTL/spi_slave.v`](RTL/spi_slave.v)
Implements the SPI slave protocol logic.  
- **Inputs**: `clk`, `rst_n`, `sclk`, `cs_n`, `mosi`
- **Outputs**: `miso`, `data_out`, `valid`, `response_ready`
- **Logic**:
  - Receives 32 bits on `mosi` (sampled on `sclk` rising edge).
  - When 32 bits are received, asserts `valid`, latches data, and prepares a response (`data + 1`).
  - Shifts out response on `miso` (on `sclk` falling edge).
  - Asserts `response_ready` when response is loaded.

#### [`RTL/spi_top.v`](RTL/spi_top.v)
Top-level module connecting `device_a` (master) and `device_b` (slave) via SPI signals.  
- **Inputs**: `clk`, `rst_n`, `in_data_A`
- **Outputs**: `out_data_B`, `out_data_A`, `done_A_to_B`, `response_ready`, `done_B_to_A`
- **Role**: Wires up the SPI bus, exposes key signals for testbenches.

#### [`RTL/tb_spi_top.v`](RTL/tb_spi_top.v)
Traditional Verilog testbench for waveform-based simulation.  
- **Generates**: Clock, reset, random input data.
- **Checks**: That `device_b` receives the correct value and `device_a` receives the incremented response.
- **Waveform**: Dumps VCD for viewing in waveform viewers.

---

### Python Testbench and Interface

#### [`test_device_a.py`](test_device_a.py)
Cocotb-based Python testbench for `device_b` (the SPI slave).  
- **Test**: `spi_roundtrip_fsm_test`
- **Behavior**: 
  - Emulates the FSM of `device_a` in Python, driving SPI signals to the DUT (`device_b`).
  - Loads input data from the `TX_DATA` environment variable.
  - Drives SPI protocol, waits for `response_ready`, then reads back the incremented value.
  - Asserts correctness and logs detailed debug info.
- **Role**: Used as the main test module for cocotb simulation (see Makefile).

#### [`hw_spi_interface.py`](hw_spi_interface.py)
Python interface to automate hardware simulation and extract results.  
- **Function**: `hw_spi_call(input_hex)`
- **Behavior**:
  - Sets the `TX_DATA` environment variable.
  - Runs `make` (which triggers cocotb simulation).
  - Parses cocotb output for the received value using regex.
  - Returns the received value as an integer.
- **Role**: Allows Python scripts to interact with the hardware simulation as a function call.

#### [`test_tx_rx_spi.py`](test_tx_rx_spi.py)
Python script for stress-testing the SPI channel.  
- **Behavior**:
  - Generates 10 random floating-point numbers.
  - Converts each to 32-bit hex, sends via `hw_spi_call`, expects the incremented value.
  - Checks correctness, prints detailed scoreboard and timing.
- **Role**: High-level system test, exercises the full simulation flow.

---

### Simulation and Build Artifacts

#### [`Makefile`](Makefile)
Makefile for running cocotb-based simulation with Icarus Verilog.  
- **Defines**:
  - `TOPLEVEL`: Top-level Verilog module for simulation (`device_b`).
  - `MODULE`: Python test module (`test_device_a`).
  - `VERILOG_SOURCES`: List of Verilog source files.
  - Includes cocotb's simulation makefile.
- **Role**: Orchestrates build and simulation, invoked by Python scripts.

#### [`sim_build/`](sim_build/)
- **sim.vvp**: Compiled simulation executable (Icarus Verilog).
- **device_b.fst**: Fast waveform dump for GTKWave.
- **cocotb_iverilog_dump.v**: Helper for waveform dumping.
- **cmds.f**: Timescale configuration for simulation.

---

## Detailed Data Flow

1. **Test Initiation**:
   - `test_tx_rx_spi.py` generates a random float, converts it to 32-bit hex, and calls `hw_spi_call()`.

2. **Simulation Launch**:
   - `hw_spi_call()` sets `TX_DATA` and runs `make`, which triggers cocotb simulation using [`test_device_a.py`](test_device_a.py) as the testbench.

3. **Cocotb Testbench**:
   - `test_device_a.py` emulates the FSM of `device_a` in Python, driving SPI signals to the DUT (`device_b`).
   - The Verilog DUT is [`device_b`](RTL/device_b.v), which instantiates [`spi_slave`](RTL/spi_slave.v).

4. **SPI Transaction**:
   - The Python testbench sends the 32-bit value over SPI to `device_b`.
   - `device_b` receives the value, increments it, and prepares the response.
   - The testbench then clocks out the response from `device_b` over SPI.

5. **Result Extraction**:
   - The cocotb testbench logs the received value.
   - `hw_spi_call()` parses the cocotb output and returns the value to `test_tx_rx_spi.py`.

6. **Verification**:
   - `test_tx_rx_spi.py` checks if the received value matches the expected incremented value, logs results, and prints a scoreboard.

---

## How to Run the Project

### Prerequisites

- Python 3.x
- cocotb
- Icarus Verilog (`iverilog`)
- Make

### Running the Stress Test

1. **Install dependencies** (if not already installed):

   ```sh
   pip install cocotb
   sudo apt-get install iverilog make
   ```

2. **Run the Python stress test**:

   ```sh
   python test_tx_rx_spi.py
   ```

   This will:
   - Generate random floats.
   - For each, run a cocotb simulation, sending the value to the Verilog SPI slave.
   - Print a detailed scoreboard of results.

3. **View Waveforms** (optional):

   - After running, open the generated waveform file (e.g., `sim_build/device_b.fst` or `spi_waveform.vcd`) in GTKWave for debugging.

---

## Testing and Verification

- **Functional Verification**:  
  - The main test is `spi_roundtrip_fsm_test` in [`test_device_a.py`](test_device_a.py), which checks that the SPI slave increments the received value and returns it correctly.
  - The stress test in [`test_tx_rx_spi.py`](test_tx_rx_spi.py) runs this check for multiple random values.

- **Waveform Debugging**:  
  - Use [`RTL/tb_spi_top.v`](RTL/tb_spi_top.v) for traditional Verilog simulation and waveform viewing.
  - Use cocotb's logging and generated waveforms for debugging Python-driven simulations.

---

## Results
```bash
❯ iverilog RTL/tb_spi_top.v -y ./RTL/ && vvp a.out
VCD info: dumpfile spi_waveform.vcd opened for output.
=== Bi-Directional SPI Round Trip Test ===
[TB] Sending data to B: 0x3f004089
[TB] B received      : 0x3f004089
[TB] A received reply: 0x3f00408a
SPI transfer time: 2740000 ns for 32 bits (4 Bytes) data
[PASS] Round-trip SPI exchange successful!
SPI throughput = 11.68 Mbps
RTL/tb_spi_top.v:102: $finish called at 2850000 (1ps)

```

- The SPI Benchmark shows I can send and receive 32 bits data in – **2.74 ms**
- So one-way latency per word = 2.74 ms / 2 = **1.37 ms**
---

## How Everything Connects

- **SPI Protocol**:  
  - `device_a` (master) and `device_b` (slave) communicate over SPI using shared signals: `sclk`, `mosi`, `miso`, `cs_n`.
  - `spi_master.v` and `spi_slave.v` implement the protocol logic for each side.

- **Top-Level Integration**:  
  - `spi_top.v` connects both devices and exposes their interfaces for testbenches.

- **Testing**:  
  - Python cocotb testbench (`test_device_a.py`) emulates the master, drives the slave, and checks results.
  - The Python interface (`hw_spi_interface.py`) allows high-level scripts to automate simulation and extract results.
  - The stress test (`test_tx_rx_spi.py`) repeatedly exercises the full stack.

- **Build and Simulation**:  
  - The Makefile automates compilation and simulation, integrating cocotb and Icarus Verilog.

---