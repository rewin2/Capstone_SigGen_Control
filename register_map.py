# register_map.py
#
# Complete register address map for TI LMX2820
#
# Philosophy:
# - ALL registers (R0–R122) are defined
# - Only registers actively used have bitfields defined
# - Reserved registers are intentionally opaque
#
# This prevents accidental register clobbering while
# allowing safe expansion later.


# ============================================================
# Register Addresses (R0 – R122)
# ============================================================

# --- System / control ---
R0   = 0
R1   = 1
R2   = 2
R3   = 3
R4   = 4
R5   = 5
R6   = 6
R7   = 7
R8   = 8
R9   = 9
R10  = 10
R11  = 11
R12  = 12
R13  = 13
R14  = 14
R15  = 15
R16  = 16
R17  = 17
R18  = 18
R19  = 19
R20  = 20
R21  = 21
R22  = 22
R23  = 23
R24  = 24
R25  = 25
R26  = 26
R27  = 27
R28  = 28
R29  = 29
R30  = 30
R31  = 31
R32  = 32
R33  = 33
R34  = 34
R35  = 35

# --- PLL core ---
R_PLL_N     = 36
R_PLL_NUM   = 37
R_PLL_DEN   = 38

# --- Output / divider ---
R_CHDIV     = 39
R_OUTA_MUX  = 40
R_RFOUTA_PWR = 41
R_RFOUTA_EN  = 42

# --- Reserved / intermediate ---
R43 = 43
R44 = 44
R45 = 45
R46 = 46
R47 = 47
R48 = 48
R49 = 49
R50 = 50
R51 = 51
R52 = 52
R53 = 53
R54 = 54
R55 = 55
R56 = 56
R57 = 57
R58 = 58
R59 = 59
R60 = 60
R61 = 61
R62 = 62
R63 = 63
R64 = 64
R65 = 65
R66 = 66
R67 = 67
R68 = 68
R69 = 69
R70 = 70
R71 = 71
R72 = 72
R73 = 73
R74 = 74
R75 = 75
R76 = 76
R77 = 77

# --- Calibration / status ---
R_VCO_CAL  = 78
R79 = 79
R80 = 80
R81 = 81
R82 = 82
R83 = 83
R84 = 84
R85 = 85
R86 = 86
R87 = 87
R88 = 88
R89 = 89
R90 = 90
R91 = 91
R92 = 92
R93 = 93
R94 = 94
R95 = 95
R96 = 96
R97 = 97
R98 = 98
R99 = 99
R100 = 100
R101 = 101
R102 = 102
R103 = 103
R104 = 104
R105 = 105
R106 = 106
R107 = 107
R108 = 108
R109 = 109
R110 = 110
R111 = 111
R112 = 112
R113 = 113
R114 = 114
R115 = 115
R116 = 116
R117 = 117
R118 = 118
R119 = 119
R120 = 120
R121 = 121
R122 = 122


# ============================================================
# Bitfield Definitions (ONLY where used)
# (mask, shift)
# ============================================================

# --- R36: PLL_N ---
PLL_N_MASK   = 0xFFFF
PLL_N_SHIFT  = 0

# --- R37: PLL_NUM ---
PLL_NUM_MASK  = 0xFFFFFF
PLL_NUM_SHIFT = 0

# --- R38: PLL_DEN ---
PLL_DEN_MASK  = 0xFFFFFF
PLL_DEN_SHIFT = 0

# --- R39: Channel Divider ---
CHDIV_MASK   = 0x07
CHDIV_SHIFT  = 0

# --- R40: Output Mux ---
OUTA_MUX_MASK  = 0x03
OUTA_MUX_SHIFT = 0

# --- R41: RFOUTA Power ---
RFOUTA_PWR_MASK  = 0x3F
RFOUTA_PWR_SHIFT = 0

# --- R42: RFOUTA Enable ---
RFOUTA_EN_MASK  = 0x01
RFOUTA_EN_SHIFT = 0


# ============================================================
# Helper Functions
# ============================================================

def set_field(reg_value, mask, shift, field_value):
    """
    Safely update a bitfield within a register value.
    """
    reg_value &= ~(mask << shift)
    reg_value |= (field_value & mask) << shift
    return reg_value


def get_field(reg_value, mask, shift):
    """
    Extract a bitfield from a register value.
    """
    return (reg_value >> shift) & mask
