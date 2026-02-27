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

F_REF_HZ = 50_000_000
STEP_HZ  = 100_000_000
VCO_MIN  = 5_650_000_000
VCO_MAX  = 11_300_000_000

class FrequencyPlanError(Exception):
    pass


# ------------------------------------------------------------
# Frequency Planner (Integer-N)
# ------------------------------------------------------------

def compute_frequency_plan_integer_n(freq_hz: int) -> dict:

    freq_hz = round(freq_hz)

    if not (1_000_000_000 <= freq_hz <= 40_000_000_000):
        raise ValueError("Frequency must be between 1 and 40 GHz")

    if freq_hz % STEP_HZ != 0:
        raise ValueError("Frequency must be in 100 MHz steps")

    external_doubler = False
    chdiv            = None

    # --------------------------------------------------
    # Band 1: 1–5.65 GHz — divider path
    # --------------------------------------------------
    if freq_hz <= 5_650_000_000:
        band     = "1_10"
        outa_mux = 0

        for div in [2, 4, 8, 16, 32, 64, 128]:
            vco_hz = freq_hz * div
            if VCO_MIN <= vco_hz <= VCO_MAX:
                chdiv = div
                break
        else:
            raise FrequencyPlanError("No valid CHDIV for frequency")

    # --------------------------------------------------
    # Band 1 continued: 5.65–10 GHz — direct VCO
    # --------------------------------------------------
    elif freq_hz <= 10_000_000_000:
        band     = "1_10"
        outa_mux = 1
        vco_hz   = freq_hz

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError("VCO out of range in 5.65-10 GHz range")

    # --------------------------------------------------
    # Band 2: 10–11.3 GHz — direct VCO
    # --------------------------------------------------
    elif freq_hz <= 11_300_000_000:
        band     = "10_22"
        outa_mux = 1
        vco_hz   = freq_hz

    # --------------------------------------------------
    # Band 2: 11.3–22.6 GHz — internal doubler
    # --------------------------------------------------
    elif freq_hz <= 22_600_000_000:
        band     = "10_22"
        outa_mux = 2
        vco_hz   = freq_hz // 2

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError("VCO out of range in 11.3-22.6 GHz range")

    # --------------------------------------------------
    # Band 3: 22.6–30 GHz — internal + external doubler
    # --------------------------------------------------
    elif freq_hz <= 30_000_000_000:
        band             = "22_30"
        outa_mux         = 2
        external_doubler = True
        vco_hz           = freq_hz // 4

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError("VCO out of range in 22.6-30 GHz range")

    # --------------------------------------------------
    # Band 4: 30–40 GHz — internal + external doubler
    # --------------------------------------------------
    else:
        band             = "30_40"
        outa_mux         = 2
        external_doubler = True
        vco_hz           = freq_hz // 4

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError("VCO out of range in 30-40 GHz range")

    # --------------------------------------------------
    # Integer-N calculation
    # --------------------------------------------------
    if vco_hz % F_REF_HZ != 0:
        raise FrequencyPlanError("VCO frequency is not an integer multiple of reference")

    pll_n = vco_hz // F_REF_HZ

    if not (12 <= pll_n <= 0x7FFF):
        raise FrequencyPlanError(f"PLL N={pll_n} out of valid range (12–32767)")

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
    print(f"CHDIV = {chdiv}")
    print(f"OUTA_MUX = {outa_mux}")

    return {
        "N": pll_n,
        "chdiv": chdiv,
        "outa_mux": outa_mux,
        "band": band,
        "power": power,
        "external_doubler": external_doubler,
    }
