# write_order.py
#
# LMX2820 register write-ordering definitions
#
# These lists define STRICT hardware sequencing rules.
# No logic belongs here.


from register_map import *


# ============================================================
# Static configuration registers
# Written once after reset
# ============================================================

STATIC_REGS = [
    SYS_CTRL_REG,
    SYS_PWR_REG,
    SYS_RESET_REG,
    REF_CTRL_REG,
    REF_DIV_REG,
    VCO_BIAS_REG,
    VCO_GAIN_REG,
    # Add other always-static registers here
]


# ============================================================
# Frequency-defining registers
# Written on EVERY frequency change
# ============================================================

FREQ_REGS = [

    # --------------------------------------------------------
    # Integer Divider N (write LSB → MSB)
    # --------------------------------------------------------
    PLL_N_LSB_REG,
    PLL_N_MSB_REG,

    # --------------------------------------------------------
    # Fractional Numerator (NUM) (LSB → MSB)
    # --------------------------------------------------------
    PLL_NUM_LSB_REG,
    PLL_NUM_MSB_REG,

    # --------------------------------------------------------
    # Fractional Denominator (DEN) (LSB → MSB)
    # --------------------------------------------------------
    PLL_DEN_LSB_REG,
    PLL_DEN_MSB_REG,

    # --------------------------------------------------------
    # Fractional mode control
    # Must be written BEFORE calibration
    # --------------------------------------------------------
    PLL_FRAC_CTRL_REG,

    # --------------------------------------------------------
    # Channel Divider
    # --------------------------------------------------------
    CHDIV_REG,

    # --------------------------------------------------------
    # Output mux selection
    # --------------------------------------------------------
    OUTA_MUX_REG,
]


# ============================================================
# Calibration trigger registers
# Written AFTER all frequency registers
# ============================================================

CAL_REGS = [
    VCO_CAL_CTRL_REG,
]


# ============================================================
# RF output enable / power
# Written LAST, after lock
# ============================================================

OUTPUT_REGS = [
    RFOUTA_PWR_REG,
    RFOUTA_EN_REG,
]
