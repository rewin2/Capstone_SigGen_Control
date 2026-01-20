# register_map.py
#
# LMX2820 Register Map (Datasheet-Aligned Semantic Names)
#
# IMPORTANT:
# - Numeric addresses are authoritative
# - Names reflect documented function only
# - Undocumented registers remain RESERVED


# ============================================================
# System / Device Control
# ============================================================

SYS_CTRL_REG             = 0    # R0  System control
SYS_PWR_REG              = 1    # R1  Power control
SYS_RESET_REG            = 2    # R2  Reset control


# ============================================================
# Reference Path
# ============================================================

REF_CTRL_REG             = 10   # R10 Reference input control
REF_DIV_REG              = 11   # R11 Reference divider


# ============================================================
# PLL Core
# ============================================================

# Integer Divider N (19 bits)
PLL_N_LSB_REG = 36   # R36 N[15:0]
PLL_N_MSB_REG = 37   # R37 N[18:16]

# Fractional Numerator (24 bits)
PLL_NUM_LSB_REG = 38  # R38 NUM[15:0]
PLL_NUM_MSB_REG = 39  # R39 NUM[23:16]

# Fractional Denominator (24 bits)
PLL_DEN_LSB_REG = 40  # R40 DEN[15:0]
PLL_DEN_MSB_REG = 41  # R41 DEN[23:16]

# Fractional Mode Control
PLL_FRAC_CTRL_REG = 42
PLL_FRAC_EN_MASK  = 0x1
PLL_FRAC_EN_SHIFT = 0

# ============================================================
# Output / Divider Path
# ============================================================

CHDIV_REG                = 39   # R39 Channel divider
OUTA_MUX_REG             = 40   # R40 RFOUTA mux select
RFOUTA_PWR_REG           = 41   # R41 RFOUTA output power
RFOUTA_EN_REG            = 42   # R42 RFOUTA enable


# ============================================================
# VCO / Calibration
# ============================================================

VCO_CAL_CTRL_REG         = 78   # R78 VCO calibration control
VCO_BIAS_REG             = 79   # R79 VCO bias control
VCO_GAIN_REG             = 80   # R80 VCO gain control


# ============================================================
# Status / Lock Detect
# ============================================================

PLL_STATUS_REG           = 82   # R82 PLL status / lock detect


# ============================================================
# Reserved Registers
# ============================================================

RESERVED_REGS = set(range(123)) - {
    SYS_CTRL_REG,
    SYS_PWR_REG,
    SYS_RESET_REG,
    REF_CTRL_REG,
    REF_DIV_REG,
    PLL_N_REG,
    PLL_NUM_REG,
    PLL_DEN_REG,
    CHDIV_REG,
    OUTA_MUX_REG,
    RFOUTA_PWR_REG,
    RFOUTA_EN_REG,
    VCO_CAL_CTRL_REG,
    VCO_BIAS_REG,
    VCO_GAIN_REG,
    PLL_STATUS_REG,
}


# ============================================================
# Bitfield Definitions (only where used)
# ============================================================

# --- PLL_N_REG ---
PLL_N_MASK    = 0xFFFF
PLL_N_SHIFT   = 0

# --- PLL_NUM_REG ---
PLL_NUM_MASK  = 0xFFFFFF
PLL_NUM_SHIFT = 0

# --- PLL_DEN_REG ---
PLL_DEN_MASK  = 0xFFFFFF
PLL_DEN_SHIFT = 0

# --- CHDIV_REG ---
CHDIV_MASK    = 0x07
CHDIV_SHIFT   = 0

# --- OUTA_MUX_REG ---
OUTA_MUX_MASK  = 0x03
OUTA_MUX_SHIFT = 0

# --- RFOUTA_PWR_REG ---
RFOUTA_PWR_MASK  = 0x3F
RFOUTA_PWR_SHIFT = 0

# --- RFOUTA_EN_REG ---
RFOUTA_EN_MASK   = 0x01
RFOUTA_EN_SHIFT  = 0


# ============================================================
# Helper Functions
# ============================================================

def set_field(reg_value, mask, shift, field_value):
    reg_value &= ~(mask << shift)
    reg_value |= (field_value & mask) << shift
    return reg_value


def get_field(reg_value, mask, shift):
    return (reg_value >> shift) & mask
