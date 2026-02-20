# frequency_plan.py
#
# Fractional-N frequency planner for LMX2820
#
# Responsibilities:
# - Validate requested frequency
# - Select band and signal path
# - Compute VCO frequency
# - Compute integer PLL N
# - Compute fractional NUM / DEN
# - Select legal channel divider
#
# Does NOT:
# - Touch registers
# - Control GPIO
# - Know about FSM or SPI


# ------------------------------------------------------------
# Constants
# ------------------------------------------------------------

F_REF_HZ = 200_000_000      # 200 MHz reference (corrected comment)

# LMX2820 VCO range
VCO_MIN = 5_650_000_000
VCO_MAX = 11_300_000_000

# Fractional resolution (24-bit typical for LMX2820)
FRAC_DEN = 2**24

class FrequencyPlanError(Exception):
    pass


# ------------------------------------------------------------
# Frequency Planner (Fractional-N)
# ------------------------------------------------------------

def compute_frequency_plan_fractional(freq_hz: float) -> dict:

    if freq_hz < 1_000_000_000 or freq_hz > 40_000_000_000:
        raise ValueError("Frequency must be between 1 and 40 GHz")

    # -------------------------------------------------
    # Output path selection (UNCHANGED)
    # -------------------------------------------------

    external_doubler = False

    if freq_hz <= 10_000_000_000:
        band = "1_10"
        outa_mux = 0  # divider path
        possible_dividers = [2, 4, 8, 16, 32, 64, 128]
        external_doubler = None

        for div in possible_dividers:
            vco_hz = freq_hz * div
            if VCO_MIN <= vco_hz <= VCO_MAX:
                chdiv = div
                break
        else:
            raise FrequencyPlanError("No valid divider for 1-10 GHz")

    elif freq_hz <= 11_300_000_000:
        band = "10_22"
        outa_mux = 1  # direct
        chdiv = None
        external_doubler = None
        vco_hz = freq_hz

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError("VCO out of range (direct mode)")

    elif freq_hz <= 22_600_000_000:
        band = "10_22"
        outa_mux = 2  # internal ×2
        chdiv = None
        external_doubler = None
        vco_hz = freq_hz / 2

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError("VCO out of range (×2 mode)")

    else:
        band = "22_40"
        outa_mux = 2  # internal ×2
        external_doubler = True
        chdiv = None
        vco_hz = freq_hz / 4

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError("VCO out of range (×4 mode)")

    # -------------------------------------------------
    # Fractional-N PLL calculation
    # -------------------------------------------------

    f_pfd = F_REF_HZ

    n_float = vco_hz / f_pfd
    pll_n = int(n_float)

    frac = n_float - pll_n
    num = int(round(frac * FRAC_DEN))
    den = FRAC_DEN

    # Handle rounding rollover
    if num == den:
        pll_n += 1
        num = 0

    if pll_n < 1:
        raise FrequencyPlanError("Invalid PLL N")

    fractional = (num != 0)

    # -------------------------------------------------
    # Power (max for now)
    # -------------------------------------------------

    power = 0x7

    # -------------------------------------------------
    # Debug
    # -------------------------------------------------

    print(f"Requested = {freq_hz/1e9:.6f} GHz")
    print(f"VCO = {vco_hz/1e9:.6f} GHz")
    print(f"N = {pll_n}")
    print(f"NUM = {num}")
    print(f"DEN = {den}")
    print(f"Fractional = {fractional}")
    print(f"CHDIV = {chdiv}")
    print(f"OUTA_MUX = {outa_mux}")

    return {
        "N": pll_n,
        "NUM": num,
        "DEN": den,
        "fractional": fractional,
        "chdiv": chdiv,
        "outa_mux": outa_mux,
        "band": band,
        "power": power,
        "external_doubler": external_doubler,
    }
