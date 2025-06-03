import subprocess
import re

def hw_spi_call(input_hex):
    # Format the input hex and pass it as environment variable to make
    hex_str = f"0x{input_hex:08X}"
    env = {"TX_DATA": hex_str}

    print(f"[INFO] Sending: {hex_str}")
    try:
        result = subprocess.run(
            ["make"],
            text=True,
            capture_output=True,
            env={**env, **dict(**subprocess.os.environ)},
            timeout=10
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Cocotb simulation timed out.")

    # Log output for debug
    # print(result.stdout)

    # Search output value in cocotb logs
    match = re.search(r"\[TB\] Received\s+: 0x([0-9A-Fa-f]+)", result.stdout)
    if not match:
        raise RuntimeError("Could not extract received value from cocotb output.")

    received_hex = int(match.group(1), 16)
    print(f"[INFO] Received: 0x{received_hex:08X}")
    return received_hex
