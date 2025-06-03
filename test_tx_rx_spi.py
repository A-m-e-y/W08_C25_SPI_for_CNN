import random
import struct
from hw_spi_interface import hw_spi_call

def float_to_hex(f):
    return struct.unpack('<I', struct.pack('<f', f))[0]

def hex_to_float(h):
    return struct.unpack('<f', struct.pack('<I', h))[0]

# Generate and send 10 random floats
for i in range(10):
    f = random.uniform(-1000, 1000)
    h = float_to_hex(f)
    h_resp = hw_spi_call(h)
    f_resp = hex_to_float(h_resp)

    print(f"\n[{i}] Sent Float     : {f:.6f}")
    print(f"[{i}] Sent Hex       : 0x{h:08X}")
    print(f"[{i}] Received Hex   : 0x{h_resp:08X}")
    print(f"[{i}] Received Float : {f_resp:.6f}")
