# write_order.py
#
# LMX2820 register write-ordering definitions
#
# These lists define STRICT hardware sequencing rules.
# No logic belongs here.
#
# Rules (from datasheet section 8.3):
#   - Registers must be written in DESCENDING order
#   - R0 must always be written LAST
#   - Writing R0 with FCAL_EN=1 triggers VCO calibration
#   - R0 must never appear in STATIC_REGS (belongs in CAL_REGS only)


from register_map import *


# ============================================================
# Static configuration registers
# Written once after reset, in descending order
# R0 is written separately by initialize_registers()
# ============================================================

STATIC_REGS = [
    VCO_GAIN_REG,      # R51
    VCO_BIAS_REG,      # R50
    REF_DIV_REG,       # R11
    REF_CTRL_REG,      # R10
    SYS_RESET_REG,     # R2
    SYS_PWR_REG,       # R1
    SYS_CTRL_REG,      # R0  ← always last, written with FCAL_EN=0
]


# ============================================================
# Frequency-defining registers
# Written on EVERY frequency change, in descending order
# ============================================================

FREQ_REGS = [

    # --------------------------------------------------------
    # Output mux selection
    # Must be written before calibration
    # --------------------------------------------------------
    OUTA_MUX_REG,       # R78

    # --------------------------------------------------------
    # INSTCAL_PLL (instant calibration value)
    # = int(2^32 * NUM/DEN)
    # In integer-N mode: always 0x0000
    # --------------------------------------------------------
    INSTCAL_MSB_REG,    # R44
    INSTCAL_LSB_REG,    # R45  (note: written after MSB per descending rule)

    # --------------------------------------------------------
    # Fractional numerator NUM
    # In integer-N mode: always 0x0000
    # --------------------------------------------------------
    PLL_NUM_MSB_REG,    # R42
    PLL_NUM_LSB_REG,    # R43

    # --------------------------------------------------------
    # Integer Divider N (single 15-bit register)
    # --------------------------------------------------------
    PLL_N_REG,          # R36

    # --------------------------------------------------------
    # MASH order control
    # Must be written before N takes effect
    # Integer mode = MASH_INTEGER (0)
    # --------------------------------------------------------
    MASH_CTRL_REG,      # R35

    # --------------------------------------------------------
    # Channel Divider
    # Only relevant when OUTA_MUX = 0 (divider path)
    # --------------------------------------------------------
    CHDIV_REG,          # R32

    # --------------------------------------------------------
    # InstaCal_2x — R1 bit 1
    # 0 = normal, 1 = doubler engaged
    # Written last before calibration trigger
    # --------------------------------------------------------
    INSTACAL_2X_REG,    # R1
]


# ============================================================
# Calibration trigger registers
# Written AFTER all frequency registers
# Writing R0 with FCAL_EN=1 triggers VCO calibration
# ============================================================

CAL_REGS = [
    VCO_CAL_CTRL_REG,   # R0 — must be last
]


# ============================================================
# RF output enable / power
# Written LAST, after PLL lock is confirmed
# ============================================================

OUTPUT_REGS = [
    RFOUTA_PWR_REG,     # R79
    RFOUTA_EN_REG,      # R78
]