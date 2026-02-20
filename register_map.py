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

# R0 fields
FCAL_EN_REG       = 0    # R0
FCAL_EN_MASK      = 0x0010   # bit 4
FCAL_EN_SHIFT     = 4

RESET_REG         = 0    # R0
RESET_MASK        = 0x0002   # bit 1
RESET_SHIFT       = 1

POWERDOWN_REG     = 0    # R0
POWERDOWN_MASK    = 0x0001   # bit 0
POWERDOWN_SHIFT   = 0


# ============================================================
# Reference Input
# ============================================================

REF_CTRL_REG      = 10   # R10
REF_DIV_REG       = 11   # R11

# R11: OSC_2X (reference doubler)
OSC_2X_REG        = 11
OSC_2X_MASK       = 0x0010   # bit 4
OSC_2X_SHIFT      = 4

# R12: MULT (reference multiplier)
MULT_REG          = 12
MULT_MASK         = 0x1C00   # bits 12:10
MULT_SHIFT        = 10

# R13: PLL_R (post-R divider)
PLL_R_REG         = 13
PLL_R_MASK        = 0x1FE0   # bits 12:5
PLL_R_SHIFT       = 5

# R14: PLL_R_PRE (pre-R divider)
PLL_R_PRE_REG     = 14
PLL_R_PRE_MASK    = 0x0FFF   # bits 11:0
PLL_R_PRE_SHIFT   = 0


# ============================================================
# PLL Core — INTEGER + FRACTIONAL
# ============================================================

# ------------------------------------------------------------
# Integer Divider N (15 bits, single register)
# Datasheet R36 Table 1-39: bits 14:0 = PLL_N
# ------------------------------------------------------------

PLL_N_REG         = 36   # R36  PLL_N[14:0]
PLL_N_MASK        = 0x7FFF
PLL_N_SHIFT       = 0

# Legacy aliases — kept for compatibility but both point to R36
PLL_N_LSB_REG     = 36
PLL_N_MSB_REG     = 36


# ------------------------------------------------------------
# Fractional Denominator DEN (32 bits)
# Datasheet R38 = DEN[31:16], R39 = DEN[15:0]
# ------------------------------------------------------------

PLL_DEN_MSB_REG   = 38   # R38  DEN[31:16]
PLL_DEN_MSB_MASK  = 0xFFFF
PLL_DEN_MSB_SHIFT = 0

PLL_DEN_LSB_REG   = 39   # R39  DEN[15:0]
PLL_DEN_LSB_MASK  = 0xFFFF
PLL_DEN_LSB_SHIFT = 0


# ------------------------------------------------------------
# MASH Seed (R40, R41) — not PLL_NUM
# Datasheet R40 = MASH_SEED[31:16], R41 = MASH_SEED[15:0]
# ------------------------------------------------------------

MASH_SEED_MSB_REG = 40   # R40  MASH_SEED[31:16]
MASH_SEED_LSB_REG = 41   # R41  MASH_SEED[15:0]


# ------------------------------------------------------------
# Fractional Numerator NUM (32 bits)
# Datasheet R42 = NUM[31:16], R43 = NUM[15:0]
# ------------------------------------------------------------

PLL_NUM_MSB_REG   = 42   # R42  NUM[31:16]
PLL_NUM_MSB_MASK  = 0xFFFF
PLL_NUM_MSB_SHIFT = 0

PLL_NUM_LSB_REG   = 43   # R43  NUM[15:0]
PLL_NUM_LSB_MASK  = 0xFFFF
PLL_NUM_LSB_SHIFT = 0


# ------------------------------------------------------------
# MASH / Fractional Mode Control
# Datasheet R35: MASH_ORDER bits 8:7, MASH_RESET_N bit 12
# ------------------------------------------------------------

MASH_CTRL_REG     = 35   # R35

MASH_ORDER_MASK   = 0x0180   # bits 8:7
MASH_ORDER_SHIFT  = 7

# MASH_ORDER values
MASH_INTEGER      = 0x0      # Integer mode
MASH_ORDER_1      = 0x1      # First order
MASH_ORDER_2      = 0x2      # Second order
MASH_ORDER_3      = 0x3      # Third order

MASH_RESET_N_MASK  = 0x1000  # bit 12
MASH_RESET_N_SHIFT = 12

# Aliases for driver compatibility
PLL_FRAC_EN_REG   = 35
PLL_FRAC_CTRL_REG = 35
PLL_FRAC_EN_MASK  = MASH_ORDER_MASK
PLL_FRAC_EN_SHIFT = MASH_ORDER_SHIFT


# ============================================================
# VCO Configuration
# ============================================================

VCO_BIAS_REG      = 50   # R50  (reserved, program default)
VCO_GAIN_REG      = 51   # R51  (reserved, program default)

# VCO Calibration: triggered by writing R0 with FCAL_EN=1
# There is no dedicated calibration trigger register.
# VCO_CAL_CTRL_REG is aliased to R0 for driver compatibility.
VCO_CAL_CTRL_REG  = 0    # R0 — write with FCAL_EN bit set


# ============================================================
# Channel Divider (Post-VCO)
# Datasheet R32: CHDIVA bits 8:6, CHDIVB bits 11:9
# ============================================================

CHDIV_REG         = 32   # R32

CHDIVA_MASK       = 0x01C0   # bits 8:6
CHDIVA_SHIFT      = 6

CHDIVB_MASK       = 0x0E00   # bits 11:9
CHDIVB_SHIFT      = 9

# Default alias (RFOUTA uses CHDIVA)
CHDIV_MASK        = CHDIVA_MASK
CHDIV_SHIFT       = CHDIVA_SHIFT

# CHDIV encoding (same for CHDIVA and CHDIVB)
# 0 = ÷2, 1 = ÷4, 2 = ÷8, 3 = ÷16, 4 = ÷32, 5 = ÷64, 6 = ÷128


# ============================================================
# Output Muxing
# Datasheet R78: OUTA_MUX bits 1:0, OUTA_PD bit 4
# ============================================================

OUTA_MUX_REG      = 78   # R78

OUTA_MUX_MASK     = 0x0003   # bits 1:0
OUTA_MUX_SHIFT    = 0

# OUTA_MUX values
OUTA_MUX_CHDIV    = 0    # Channel divider
OUTA_MUX_VCO      = 1    # Direct VCO
OUTA_MUX_DOUBLER  = 2    # VCO doubler

OUTA_PD_MASK      = 0x0010   # bit 4 (1 = power down)
OUTA_PD_SHIFT     = 4

# R79: OUTB_MUX bits 5:4, OUTB_PD bit 8
OUTB_MUX_REG      = 79   # R79
OUTB_MUX_MASK     = 0x0030   # bits 5:4
OUTB_MUX_SHIFT    = 4
OUTB_PD_MASK      = 0x0100   # bit 8
OUTB_PD_SHIFT     = 8


# ============================================================
# RF Output A Power
# Datasheet R79: OUTA_PWR bits 3:1
# ============================================================

RFOUTA_PWR_REG    = 79   # R79

RFOUTA_PWR_MASK   = 0x000E   # bits 3:1
RFOUTA_PWR_SHIFT  = 1

# R80: OUTB_PWR bits 8:6
RFOUTB_PWR_REG    = 80   # R80
RFOUTB_PWR_MASK   = 0x01C0   # bits 8:6
RFOUTB_PWR_SHIFT  = 6


# ============================================================
# RF Output A Enable (via OUTA_PD in R78)
# NOTE: OUTA_PD is active-HIGH power-down (1 = off, 0 = on)
# ============================================================

RFOUTA_EN_REG     = 78   # R78 — shared with OUTA_MUX

# Use OUTA_PD_MASK / OUTA_PD_SHIFT; invert logic in driver:
#   enable  → write 0 to OUTA_PD
#   disable → write 1 to OUTA_PD

# Legacy alias (driver must handle active-LOW sense)
RFOUTA_EN_MASK    = OUTA_PD_MASK
RFOUTA_EN_SHIFT   = OUTA_PD_SHIFT


# ============================================================
# Lock Detect / Status
# Datasheet R74: rb_LD bits 15:14
# ============================================================

LOCK_DETECT_REG   = 74   # R74

RB_LD_MASK        = 0xC000   # bits 15:14
RB_LD_SHIFT       = 14

# rb_LD values
RB_LD_LOCKED      = 0x2      # 0x2 = Locked
RB_LD_UNLOCKED    = 0x0      # 0x0 or 0x1 = Unlocked
RB_LD_INVALID     = 0x3      # 0x3 = Invalid


# ============================================================
# Double Buffering Control
# Datasheet R70
# ============================================================

DBLBUF_CTRL_REG       = 70   # R70

DBLBUF_PLL_EN_MASK    = 0x0010   # bit 4 — buffers PLL_N, NUM, DEN, etc.
DBLBUF_PLL_EN_SHIFT   = 4

DBLBUF_CHDIV_EN_MASK  = 0x0020   # bit 5 — buffers CHDIVA/B
DBLBUF_CHDIV_EN_SHIFT = 5

DBLBUF_OUTBUF_EN_MASK = 0x0040   # bit 6 — buffers OUTA_PD/OUTB_PD
DBLBUF_OUTBUF_EN_SHIFT = 6

DBLBUF_OUTMUX_EN_MASK = 0x0080   # bit 7 — buffers OUTA_MUX/OUTB_MUX
DBLBUF_OUTMUX_EN_SHIFT = 7


# ============================================================
# Register Count
# ============================================================

LMX2820_NUM_REGS  = 123