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

F_REF_HZ = 200_000_000      # 100 MHz reference
STEP_HZ  = 100_000_000      # 100 MHz frequency step

# LMX2820 VCO range
VCO_MIN = 5_650_000_000
VCO_MAX = 11_300_000_000

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

    # ------------------------------------------------------------
    # 1–10 GHz: VCO ÷ CHDIV → OUTA_MUX = 0
    # ------------------------------------------------------------
    if freq_hz <= 10_000_000_000:
        band = "1_10"
        outa_mux = 0  # divider path

        for chdiv in (1, 2, 4, 8, 16):
            vco_hz = freq_hz * chdiv
            if VCO_MIN <= vco_hz <= VCO_MAX:
                break
        else:
            raise FrequencyPlanError("No valid VCO frequency for 1–10 GHz")

    # ------------------------------------------------------------
    # 10–11.3 GHz: VCO direct → OUTA_MUX = 1
    # ------------------------------------------------------------
    elif freq_hz <= 11_300_000_000:
        band = "10_22"
        chdiv = 1
        outa_mux = 1  # direct VCO
        vco_hz = freq_hz

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError("VCO out of range (direct mode)")

    # ------------------------------------------------------------
    # 11.3–22.6 GHz: internal VCO doubler → OUTA_MUX = 2
    # ------------------------------------------------------------
    elif freq_hz <= 22_600_000_000:
        band = "10_22"
        chdiv = 1
        outa_mux = 2  # VCO ×2
        vco_hz = freq_hz / 2

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError("VCO out of range (internal doubler)")

    # ------------------------------------------------------------
    # 22.6–40 GHz: internal ×2 + external ×2
    # ------------------------------------------------------------
    else:
        band = "22_40"
        chdiv = 1
        outa_mux = 2  # VCO ×2
        external_doubler = True
        vco_hz = freq_hz / 4

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError("VCO out of range (external doubler path)")

    # ----------------------------
    # VCO + divider selection
    # ----------------------------

    # Try legal CHDIV values until VCO is in range
    for chdiv in sorted(ALLOWED_CHDIV):
        vco_hz = freq_hz * chdiv / F_REF_HZ

        if VCO_MIN <= vco_hz <= VCO_MAX:
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
    # Power
    # ----------------------------
    power = 0x7


    # ----------------------------
    # Return plan
    # ----------------------------
    print("VCO: ", vco_hz)
    print("N: ", pll_n)
    print("chdiv: ", chdiv)
    print("outa_mux: ", outa_mux)
    print("power: ", power)

    return {
        "N": pll_n,
        "chdiv": chdiv,
        "outa_mux": outa_mux,
        "band": band,
        "power": power
    }
