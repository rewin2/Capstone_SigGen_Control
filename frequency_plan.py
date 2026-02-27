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
class FrequencyPlanError(Exception):
    pass

def compute_frequency_plan_integer_n(freq_hz: int) -> dict:
    if freq_hz < 1_000_000_000 or freq_hz > 40_000_000_000:
        raise ValueError("Frequency must be between 1 and 40 GHz")

    if freq_hz % STEP_HZ != 0:
        raise ValueError("Frequency must be in 100 MHz steps")

    # -------------------------------------------------
    # Constants (should already exist in your file)
    # -------------------------------------------------
    # VCO_MIN, VCO_MAX
    # F_REF_HZ

    # -------------------------------------------------
    # Output path selection
    # -------------------------------------------------

    external_doubler = False

    if freq_hz <= 10_000_000_000:
        band = "1_10"
        outa_mux = 0  # divider path
        possible_dividers = [2, 4, 8, 16, 32, 64, 128]

        for div in possible_dividers:
            vco_hz = freq_hz * div
            if VCO_MIN <= vco_hz <= VCO_MAX:
                chdiv = div
                break
        else:
            raise FrequencyPlanError("No valid divider for 1–10 GHz")

    elif freq_hz <= 11_300_000_000:
        band = "10_22"
        outa_mux = 1  # direct
        chdiv = 2
        vco_hz = freq_hz

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError("VCO out of range (direct mode)")

    elif freq_hz <= 22_600_000_000:
        band = "10_22"
        outa_mux = 2  # internal doubler
        chdiv = 2
        vco_hz = freq_hz / 2

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError("VCO out of range (×2 mode)")

    else:
        band = "22_40"
        outa_mux = 2  # internal ×2
        external_doubler = True
        chdiv = 2
        vco_hz = freq_hz / 4

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError("VCO out of range (×4 mode)")

    # -------------------------------------------------
    # Integer-N PLL calculation
    # -------------------------------------------------

    if vco_hz % F_REF_HZ != 0:
        raise FrequencyPlanError("VCO not integer multiple of reference")

    pll_n = int(vco_hz / F_REF_HZ)

    if pll_n < 1:
        raise FrequencyPlanError("Invalid PLL N")

    # -------------------------------------------------
    # Power (max for now)
    # -------------------------------------------------

    power = 0x7

    # -------------------------------------------------
    # Debug
    # -------------------------------------------------

    print(f"VCO = {vco_hz/1e9:.3f} GHz")
    print(f"N = {pll_n}")
    print(f"CHDIV = {chdiv}")
    print(f"OUTA_MUX = {outa_mux}")

    return {
        "N": pll_n,
        "chdiv": chdiv,          # divide ratio, not encoded
        "outa_mux": outa_mux,
        "band": band,
        "power": power,
        "external_doubler": external_doubler,
    }
