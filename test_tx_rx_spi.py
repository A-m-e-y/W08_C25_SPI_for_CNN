import random
import struct
import time
from hw_spi_interface import hw_spi_call

def float_to_hex(f):
    return struct.unpack('<I', struct.pack('<f', f))[0]

def hex_to_float(h):
    return struct.unpack('<f', struct.pack('<I', h))[0]

scoreboard = []
total_start = time.time()

print("=== SPI Hardware Stress Test (10 Random Floats) ===\n")

for i in range(10):
    f = random.uniform(-1000, 1000)
    h = float_to_hex(f)
    expected_h = (h + 1) & 0xFFFFFFFF

    start = time.time()
    h_resp = hw_spi_call(h)
    end = time.time()

    f_resp = hex_to_float(h_resp)
    expected_f = hex_to_float(expected_h)

    pass_fail = "PASS" if h_resp == expected_h else "FAIL"
    scoreboard.append((i, h, expected_h, h_resp, pass_fail, end - start))

    print(f"[{i}] Sent Float     : {f:.6f}")
    print(f"[{i}] Sent Hex       : 0x{h:08X}")
    print(f"[{i}] Expected Hex   : 0x{expected_h:08X}")
    print(f"[{i}] Received Hex   : 0x{h_resp:08X}")
    print(f"[{i}] Received Float : {f_resp:.6f}")
    print(f"[{i}] Status         : {pass_fail}")
    print(f"[{i}] Time Taken     : {end - start:.4f} sec\n")

total_end = time.time()
total_time = total_end - total_start

print("\n=== Scoreboard ===")
print(f"{'Idx':<5} {'Sent Hex':>12} {'Expected':>12} {'Received':>12} {'Status':>8} {'Time (s)':>10}")
print("-" * 65)
for i, h, expected, received, status, t in scoreboard:
    print(f"{i:<5} 0x{h:08X}   0x{expected:08X}   0x{received:08X}  {status:>8} {t:10.4f}")

print(f"\nTotal Time for 10 Transfers: {total_time:.4f} sec")
