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
    VCO_GAIN_REG,    # R51
    VCO_BIAS_REG,    # R50
    REF_DIV_REG,     # R11
    REF_CTRL_REG,    # R10
    SYS_RESET_REG,   # R2
    SYS_PWR_REG,     # R1
    SYS_CTRL_REG,    # R0  ← always last
]


# ============================================================
# Frequency-defining registers
# Written on EVERY frequency change
# ============================================================


FREQ_REGS = [

    # --------------------------------------------------------
    # MASH order control (integer mode = 0)
    # Must be written before N
    # --------------------------------------------------------
    MASH_CTRL_REG,      # R35

    # --------------------------------------------------------
    # Integer Divider N (single 15-bit register)
    # --------------------------------------------------------
    PLL_N_REG,          # R36

    # --------------------------------------------------------
    # Channel Divider
    # --------------------------------------------------------
    CHDIV_REG,          # R32

    # --------------------------------------------------------
    # Output mux selection
    # --------------------------------------------------------
    OUTA_MUX_REG,       # R78
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
