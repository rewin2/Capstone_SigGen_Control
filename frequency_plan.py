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
# - Compute InstaCal_2x flag (MIT driver alignment)
#
# Does NOT:
# - Touch registers
# - Control GPIO
# - Know about FSM or SPI


# ------------------------------------------------------------
# Constants
# ------------------------------------------------------------

F_REF_HZ = 10_000_000   # 10 MHz reference
STEP_HZ  = 100_000_000  # 100 MHz output step enforcement

# LMX2820 VCO range
VCO_MIN  = 5_650_000_000
VCO_MAX  = 11_300_000_000


# ------------------------------------------------------------
# Custom exception
# ------------------------------------------------------------

class FrequencyPlanError(Exception):
    pass


# ------------------------------------------------------------
# Frequency Planner (Integer-N)
# ------------------------------------------------------------

def compute_frequency_plan_integer_n(freq_hz: int) -> dict:
    """
    Compute a complete integer-N frequency plan for the LMX2820.

    Returns a dict containing all values needed to program the device:
        N             : PLL integer divider value
        NUM           : fractional numerator (always 0 for integer-N)
        DEN           : fractional denominator (always 1 for integer-N)
        chdiv         : channel divider ratio (2–128) or None
        outa_mux      : output mux select (0=divider, 1=VCO, 2=doubler)
        band          : signal path band string
        power         : output power field value
        external_doubler : True if external doubler is in signal path
        instacal_2x   : 1 if internal doubler engaged, else 0
        instcal_pll   : instant calibration value (always 0 for integer-N)
    """

    freq_hz = round(freq_hz)

    # --------------------------------------------------
    # Range validation
    # --------------------------------------------------
    if not (1_000_000_000 <= freq_hz <= 40_000_000_000):
        raise ValueError("Frequency must be between 1 and 40 GHz")

    # --------------------------------------------------
    # Step validation
    # --------------------------------------------------
    if freq_hz % STEP_HZ != 0:
        raise FrequencyPlanError(
            f"Frequency must be in {STEP_HZ // 1_000_000} MHz steps"
        )

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
            raise FrequencyPlanError(
                f"No valid CHDIV for {freq_hz / 1e9:.3f} GHz"
            )

    # --------------------------------------------------
    # Band 1 continued: 5.65–10 GHz — direct VCO
    # --------------------------------------------------
    elif freq_hz <= 10_000_000_000:
        band     = "1_10"
        outa_mux = 1
        vco_hz   = freq_hz

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError(
                "VCO out of range in 5.65-10 GHz range"
            )

    # --------------------------------------------------
    # Band 2: 10–11.3 GHz — direct VCO
    # --------------------------------------------------
    elif freq_hz <= 11_300_000_000:
        band     = "10_22"
        outa_mux = 1
        vco_hz   = freq_hz

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError(
                "VCO out of range in 10-11.3 GHz range"
            )

    # --------------------------------------------------
    # Band 2: 11.3–22.6 GHz — internal doubler
    # --------------------------------------------------
    elif freq_hz <= 22_600_000_000:
        band     = "10_22"
        outa_mux = 2
        vco_hz   = freq_hz // 2

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError(
                "VCO out of range in 11.3-22.6 GHz range"
            )

    # --------------------------------------------------
    # Band 3: 22.6–30 GHz — internal + external doubler
    # --------------------------------------------------
    elif freq_hz <= 30_000_000_000:
        band             = "22_30"
        outa_mux         = 2
        external_doubler = True
        vco_hz           = freq_hz // 4

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError(
                "VCO out of range in 22.6-30 GHz range"
            )

    # --------------------------------------------------
    # Band 4: 30–40 GHz — internal + external doubler
    # --------------------------------------------------
    else:
        band             = "30_40"
        outa_mux         = 2
        external_doubler = True
        vco_hz           = freq_hz // 4

        if not (VCO_MIN <= vco_hz <= VCO_MAX):
            raise FrequencyPlanError(
                "VCO out of range in 30-40 GHz range"
            )

    # --------------------------------------------------
    # Integer-N PLL calculation
    # --------------------------------------------------
    if vco_hz % F_REF_HZ != 0:
        raise FrequencyPlanError(
            f"VCO {vco_hz / 1e9:.6f} GHz is not an integer multiple "
            f"of reference {F_REF_HZ / 1e6:.1f} MHz"
        )

    pll_n = vco_hz // F_REF_HZ

    if not (12 <= pll_n <= 0x7FFF):
        raise FrequencyPlanError(
            f"PLL N={pll_n} out of valid range (12–32767)"
        )

    # --------------------------------------------------
    # InstaCal_2x — set when internal doubler is engaged
    # Source: MIT Haystack Observatory driver
    # --------------------------------------------------
    instacal_2x = 1 if outa_mux == 2 else 0

    # --------------------------------------------------
    # INSTCAL_PLL — always 0 for integer-N
    # (would be int(2^32 * NUM/DEN) for fractional mode)
    # --------------------------------------------------
    instcal_pll = 0

    # --------------------------------------------------
    # Power (max for now)
    # --------------------------------------------------
    power = 0x7

    # --------------------------------------------------
    # Debug output
    # --------------------------------------------------
    print(f"Requested  = {freq_hz / 1e9:.6f} GHz")
    print(f"VCO        = {vco_hz / 1e9:.6f} GHz")
    print(f"N          = {pll_n}")
    print(f"CHDIV      = {chdiv}")
    print(f"OUTA_MUX   = {outa_mux}")
    print(f"Band       = {band}")
    print(f"Ext doubler= {external_doubler}")
    print(f"InstaCal2x = {instacal_2x}")

    return {
        "N":                pll_n,
        "NUM":              0,          # integer-N mode
        "DEN":              1,          # integer-N mode
        "chdiv":            chdiv,
        "outa_mux":         outa_mux,
        "band":             band,
        "power":            power,
        "external_doubler": external_doubler,
        "instacal_2x":      instacal_2x,
        "instcal_pll":      instcal_pll,
    }