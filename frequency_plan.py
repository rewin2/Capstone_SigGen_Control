# frequency_plan.py
#
# Integer-N frequency planner for LMX2820
#
# Responsibilities:
# - Validate requested frequency
# - Select band and signal path
# - Compute VCO frequency
# - Compute integer PLL N
# - Select legal channel divider
#
# Does NOT:
# - Touch registers
# - Control GPIO
# - Know about FSM or SPI


# ------------------------------------------------------------
# Constants
# ------------------------------------------------------------

F_REF_HZ = 100_000_000      # 100 MHz reference
STEP_HZ  = 100_000_000      # 100 MHz frequency step

# LMX2820 VCO range
VCO_MIN_HZ = 5_650_000_000
VCO_MAX_HZ = 11_300_000_000

# Allowed channel divider values
ALLOWED_CHDIV = {1, 2, 4, 8, 16}


# ------------------------------------------------------------
# Frequency Planner
# ------------------------------------------------------------

def compute_frequency_plan_integer_n(freq_hz: int) -> dict:
    """
    Compute an integer-N frequency plan for the LMX2820.

    Returns a dictionary compatible with lmx2820.py:
        {
            "N": int,
            "chdiv": int,
            "outa_mux": int,
            "band": str,
            "power": int
        }
    """

    # ----------------------------
    # Basic validation
    # ----------------------------

    if freq_hz < 1_000_000_000 or freq_hz > 40_000_000_000:
        raise ValueError("Frequency must be between 1 and 40 GHz")

    if freq_hz % STEP_HZ != 0:
        raise ValueError("Frequency must be in 100 MHz steps")

    # ----------------------------
    # Band selection
    # ----------------------------

    if freq_hz <= 10_000_000_000:
        band = "1_10"
        outa_mux = 0
        post_mult = 1

    elif freq_hz <= 22_000_000_000:
        band = "10_22"
        outa_mux = 1
        post_mult = 1

    elif freq_hz <= 32_000_000_000:
        band = "22_32"
        outa_mux = 2
        post_mult = 2   # external doubler

    else:
        band = "32_40"
        outa_mux = 3
        post_mult = 2   # external doubler

    # ----------------------------
    # VCO + divider selection
    # ----------------------------

    # Try legal CHDIV values until VCO is in range
    for chdiv in sorted(ALLOWED_CHDIV):
        vco_hz = freq_hz * chdiv / post_mult

        if VCO_MIN_HZ <= vco_hz <= VCO_MAX_HZ:
            break
    else:
        raise RuntimeError("No valid VCO configuration found")

    # ----------------------------
    # PLL N calculation (integer-N)
    # ----------------------------

    if vco_hz % F_REF_HZ != 0:
        raise RuntimeError("VCO frequency not integer-multiple of reference")

    pll_n = int(vco_hz / F_REF_HZ)

    if pll_n < 1:
        raise RuntimeError("Invalid PLL N value")

    # ----------------------------
    # Output power (static for now)
    # ----------------------------

    power = 0x20   # mid-scale default

    # ----------------------------
    # Return plan
    # ----------------------------

    return {
        "N": pll_n,
        "chdiv": chdiv,
        "outa_mux": outa_mux,
        "band": band,
        "power": power,
    }
