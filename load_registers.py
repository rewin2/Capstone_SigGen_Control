import spidev
import time

class LMX2820:
    def __init__(self):
        self.reg_image = load_register_image_from_text(
            "HexRegisterValuesInitialState.txt"
        )

def load_register_image_from_text(path, num_registers=123):
    """
    Load an LMX2820 register image from a text file.

    Expected line format:
        R<register_number> 0x<hex_value>

    Returns:
        reg_image: list[int] of length num_registers
    """
    reg_image = [0] * num_registers

    with open(path, "r") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            reg_str, value_str = parts[0], parts[1]

            # Expect register format like "R36"
            if not reg_str.startswith("R"):
                continue

            reg_num = int(reg_str[1:])
            value = int(value_str, 16)

            if not (0 <= reg_num < num_registers):
                raise ValueError(f"Register R{reg_num} out of range")

            reg_image[reg_num] = value

    return reg_image