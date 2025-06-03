import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
cocotb.logging.getLogger("cocotb").setLevel("DEBUG")


@cocotb.test()
async def spi_roundtrip_fsm_test(dut):
    """Behavioral Python model of device_a FSM interacting with device_b Verilog via SPI."""

    # Start system clock (100 MHz)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await Timer(100, units="ns")

    # Reset
    dut.rst_n.value = 0
    dut.cs_n.value = 1
    dut.sclk.value = 0
    dut.mosi.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # FSM States
    IDLE         = 0
    SEND_PHASE1  = 1
    WAIT1        = 2
    WAIT_RESP    = 3
    LOAD_DUMMY   = 4
    SEND_PHASE2  = 5
    RECEIVE      = 6
    DONE         = 7
    state = IDLE

    # SPI Master internal FSM
    SPI_IDLE     = 0
    SPI_ASSERT   = 1
    SPI_TRANSFER = 2
    SPI_DONE     = 3
    spi_state = SPI_IDLE

    # Internal registers
    tx_data = 0x12345678
    rx_shift = 0
    bit_cnt = 0
    spi_shift = 0
    spi_bit_cnt = 0
    sclk_d = 0
    hold_cs = True
    busy = False
    send_ph2 = False

    dut._log.info(f"[TB] Starting SPI roundtrip with tx_data = 0x{tx_data:08X}")

    for cycle in range(100000):  # prevent infinite loop
        await RisingEdge(dut.clk)
        sclk_rising = (int(dut.sclk.value) == 1 and sclk_d == 0)
        sclk_d = int(dut.sclk.value)

        # SPI Master FSM
        if spi_state == SPI_IDLE:
            if state in [SEND_PHASE1, SEND_PHASE2, RECEIVE]:
                spi_shift = tx_data
                spi_bit_cnt = 31
                dut.sclk.value = 0
                busy = True
                spi_state = SPI_ASSERT

        elif spi_state == SPI_ASSERT:
            dut.cs_n.value = 0
            spi_state = SPI_TRANSFER

        elif spi_state == SPI_TRANSFER:
            dut.sclk.value = int(not dut.sclk.value)

            if int(dut.sclk.value) == 0:
                dut.mosi.value = (spi_shift >> spi_bit_cnt) & 1
            else:
                if spi_bit_cnt == 0:
                    spi_state = SPI_DONE
                else:
                    spi_bit_cnt -= 1

        elif spi_state == SPI_DONE:
            dut.sclk.value = 0
            dut.mosi.value = 0
            if not hold_cs:
                dut.cs_n.value = 1
            busy = False
            spi_state = SPI_IDLE

            if state == SEND_PHASE1:
                dut._log.info("[FSM] -> WAIT1")
                state = WAIT1
            elif state == SEND_PHASE2:
                dut._log.info("[FSM] -> RECEIVE")
                bit_cnt = 0
                rx_shift = 0
                state = RECEIVE

        # Main FSM
        if state == IDLE:
            tx_data = 0x12345678
            hold_cs = True
            dut._log.info("[FSM] -> SEND_PHASE1")
            state = SEND_PHASE1

        elif state == WAIT1:
            if not busy:
                dut._log.info("[FSM] -> WAIT_RESP")
                state = WAIT_RESP

        elif state == WAIT_RESP:
            if int(dut.response_ready.value) == 1:
                dut._log.info("[FSM] -> LOAD_DUMMY")
                state = LOAD_DUMMY

        elif state == LOAD_DUMMY:
            tx_data = 0
            # dut._log.info("[FSM] -> SEND_PHASE2")
            dut._log.info("[FSM] -> RECEIVE")
            send_ph2 = True
            state = RECEIVE

        elif state == RECEIVE:
            # print(f"dut.cs_n.value = {dut.cs_n.value} and sclk_rising = {sclk_rising}")
            if send_ph2:
                bit_cnt = 0
                rx_shift = 0
                send_ph2 = False
            elif (int(dut.cs_n.value) == 0) and (int(dut.u_spi_slave.sclk_rising) == 1):
                # await RisingEdge(dut.clk)
                sampled_bit = int(dut.miso.value)
                rx_shift = ((rx_shift << 1) | sampled_bit) & 0xFFFFFFFF
                dut._log.debug(f"[RECEIVE] Bit {bit_cnt}: {sampled_bit}, dut.miso.value: {dut.miso.value}, Shift Reg: {rx_shift:08X}")
                # print(f"{dut._sim_time}ns : MISO={sampled_bit}, rx_shift={rx_shift:08X}")
                bit_cnt += 1
                if bit_cnt == 32:
                    dut._log.info("[FSM] -> DONE")
                    state = DONE

        elif state == DONE:
            dut.cs_n.value = 1
            hold_cs = False
            break

    # Final check
    expected = (0x12345678 + 1) & 0xFFFFFFFF
    dut._log.info(f"[TB] Received  : 0x{rx_shift:08X}")
    dut._log.info(f"[TB] Expected  : 0x{expected:08X}")
    assert rx_shift == expected, "[FAIL] SPI response does not match expected value"
    dut._log.info("[PASS] SPI roundtrip test passed.")
