# register_map.py
#
# LMX2820 Register Map (Datasheet-Aligned, Semantic)
#
# Source: TI LMX2820 Datasheet (SNAU251A)
#
# This file defines:
#   - Register addresses
#   - Bit masks and shifts
#   - NO logic
#   - NO behavior
#
# It is the single source of truth for register meaning.


# ============================================================
# Helper: Bitfield utility (used by driver)
# ============================================================

def set_field(reg_val, mask, shift, value):
    reg_val &= ~mask
    reg_val |= (value << shift) & mask
    return reg_val


# ============================================================
# System / Reset / Power
# ============================================================

SYS_CTRL_REG      = 0    # R0
SYS_PWR_REG       = 1    # R1
SYS_RESET_REG     = 2    # R2

# (Masks omitted unless actively used)


# ============================================================
# Reference Input
# ============================================================

REF_CTRL_REG      = 10   # R10
REF_DIV_REG       = 11   # R11


# ============================================================
# PLL Core — INTEGER + FRACTIONAL
# ============================================================

# ------------------------------------------------------------
# Integer Divider N (19 bits total)
# ------------------------------------------------------------

PLL_N_LSB_REG     = 36   # R36  N[15:0]
PLL_N_MSB_REG     = 37   # R37  N[18:16]

PLL_N_LSB_MASK    = 0x0007
PLL_N_LSB_SHIFT   = 0

PLL_N_MSB_MASK    = 0x0007
PLL_N_MSB_SHIFT   = 0


# ------------------------------------------------------------
# Fractional Numerator NUM (24 bits)
# ------------------------------------------------------------

PLL_NUM_LSB_REG   = 38   # R38  NUM[15:0]
PLL_NUM_MSB_REG   = 39   # R39  NUM[23:16]


# ------------------------------------------------------------
# Fractional Denominator DEN (24 bits)
# ------------------------------------------------------------

PLL_DEN_LSB_REG   = 40   # R40  DEN[15:0]
PLL_DEN_MSB_REG   = 41   # R41  DEN[23:16]


# ------------------------------------------------------------
# Fractional Mode Control
# ------------------------------------------------------------

PLL_FRAC_CTRL_REG = 42   # R42

PLL_FRAC_EN_MASK  = 0x0001
PLL_FRAC_EN_SHIFT = 0


# ============================================================
# VCO Configuration
# ============================================================

VCO_BIAS_REG      = 50   # R50
VCO_GAIN_REG      = 51   # R51

VCO_CAL_CTRL_REG  = 52   # R52


# ============================================================
# Channel Divider (Post-VCO)
# ============================================================

CHDIV_REG         = 60   # R60

CHDIV_MASK        = 0x0007
CHDIV_SHIFT       = 0


# ============================================================
# Output Muxing
# ============================================================

OUTA_MUX_REG      = 61   # R61

OUTA_MUX_MASK     = 0x0003
OUTA_MUX_SHIFT    = 0


# ============================================================
# RF Output A Control
# ============================================================

RFOUTA_PWR_REG    = 70   # R70

RFOUTA_PWR_MASK   = 0x003F
RFOUTA_PWR_SHIFT  = 0


RFOUTA_EN_REG     = 71   # R71

RFOUTA_EN_MASK    = 0x0001
RFOUTA_EN_SHIFT   = 0


# ============================================================
# Lock Detect / Status
# ============================================================

LOCK_DETECT_REG   = 80   # R80
# (Typically read via GPIO instead)


# ============================================================
# Register Count
# ============================================================

LMX2820_NUM_REGS  = 123
