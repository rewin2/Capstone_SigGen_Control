# write_order.py
#
# LMX2820 register write-order definitions
#
# IMPORTANT:
# - These are hardware sequencing rules
# - No logic belongs here
# - Order matters


from register_map import *


# ============================================================
# A) Static configuration registers
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
    # (others from default image as needed)
]


# ============================================================
# B) Frequency-defining registers
# Written on every frequency change
# ============================================================

FREQ_REGS = [
    PLL_NUM_REG,    # Always write NUM first
    PLL_DEN_REG,
    PLL_N_REG,
    CHDIV_REG,
    OUTA_MUX_REG,
]


# ============================================================
# C) Calibration / trigger registers
# Written AFTER frequency registers
# ============================================================

CAL_REGS = [
    VCO_CAL_CTRL_REG,
]


# ============================================================
# D) Output enable registers
# Written LAST, after lock
# ============================================================

OUTPUT_REGS = [
    RFOUTA_PWR_REG,
    RFOUTA_EN_REG,
]
