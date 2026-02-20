# utils.py
#
# Utility functions for LMX2820 support code
#
# Responsibilities:
# - Load register image from text file
# - Validate register image size
# - Provide small reusable helpers
#
# Does NOT:
# - Touch hardware
# - Know about FSM states
# - Know about PLL math


def load_register_file(path, num_registers=123):
    """
    Load a register image from a text file.

    Expected format per line:
        R<register_number> 0x<hex_value>

    Example:
        R36  0x0028
        R78  0x0002

    Blank lines and lines starting with '#' are ignored.

    Returns:
        list[int]: register image array
    """

    reg_image = [0] * num_registers

    with open(path, "r") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) < 2:
                raise ValueError(
                    f"Invalid format on line {line_num}: '{line}'"
                )

            reg_str, value_str = parts[0], parts[1]

            if not reg_str.startswith("R"):
                raise ValueError(
                    f"Invalid register name on line {line_num}: '{reg_str}'"
                )

            try:
                reg_num = int(reg_str[1:])
            except ValueError:
                raise ValueError(
                    f"Invalid register number on line {line_num}: '{reg_str}'"
                )

            if not (0 <= reg_num < num_registers):
                raise ValueError(
                    f"Register R{reg_num} out of range on line {line_num}"
                )

            try:
                value = int(value_str, 16)
            except ValueError:
                raise ValueError(
                    f"Invalid hex value on line {line_num}: '{value_str}'"
                )

            reg_image[reg_num] = value

    return reg_image


def diff_register_images(old, new):
    """
    Compare two register images.

    Returns:
        list of tuples: (reg, old_value, new_value)
    """
    if len(old) != len(new):
        raise ValueError("Register images must be same length")

    diffs = []
    for i, (a, b) in enumerate(zip(old, new)):
        if a != b:
            diffs.append((i, a, b))

    return diffs


def format_register_diff(diffs):
    """
    Format register diffs for printing/logging.
    """
    lines = []
    for reg, old, new in diffs:
        lines.append(
            f"R{reg:03d}: 0x{old:06X} → 0x{new:06X}"
        )
    return "\n".join(lines)