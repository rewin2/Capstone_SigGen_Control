# init_register_values.py
#
# LMX2820 default register values
#
# Source: TI HexRegisterValuesInitialState.txt (16-bit data fields only)
#         Cross-referenced with MIT Haystack Observatory LMX2820 driver
#
# These are the TI power-on default values for all 123 registers.
# The address byte has been stripped — values are 16-bit data only.
#
# Key registers modified from raw TI defaults:
#   R0:  FCAL_EN cleared (bit 4 = 0) — calibration triggered separately
#   R78: OUTA_MUX=1 (VCO direct), OUTA_PD=0 (output active)
#   R79: OUTB powered down, OUTA at max power
#
# Written in descending order (R122→R0) per datasheet section 8.3.

from register_map import *

INIT_REG_VALUES = {
    122: 0x0000,
    121: 0x0000,
    120: 0x0000,
    119: 0x0009,   # captured from TICS Pro
    118: 0x0000,
    117: 0x0000,
    116: 0xF655,   # captured from TICS Pro
    115: 0x358A,   # captured from TICS Pro
    114: 0xC01A,   # captured from TICS Pro
    113: 0x8A36,   # captured from TICS Pro
    112: 0xFFFF,
    111: 0x0000,
    110: 0x001F,
    109: 0x0000,
    108: 0x0000,
    107: 0x0000,
    106: 0x0000,
    105: 0x000A,
    104: 0x0014,
    103: 0x0014,
    102: 0x0028,
    101: 0x03E8,
    100: 0x0533,
    99:  0x19B9,
    98:  0x1C80,
    97:  0x0000,
    96:  0x17F8,
    95:  0x0000,
    94:  0x0000,
    93:  0x1000,
    92:  0x0000,
    91:  0x0000,
    90:  0x0000,
    89:  0x0000,
    88:  0x03FF,
    87:  0xFF00,
    86:  0x0040,
    85:  0x0000,
    84:  0x0040,
    83:  0x0F00,
    82:  0x0000,
    81:  0x0000,
    80:  0x01C0,   # OUTB max power
    79:  0x011E,   # OUTB powered down, OUTA max power (MIT driver value)
    78:  0x0001,   # OUTA_MUX=VCO(1), OUTA_PD=0 (enabled) (MIT driver value)
    77:  0x0608,   # Mute pin polarity
    76:  0x0000,
    75:  0x1128,   # captured from TICS Pro
    74:  0x87A5,   # captured from TICS Pro
    73:  0x0000,   # captured from TICS Pro
    72:  0x0008,   # captured from TICS Pro
    71:  0x8201,   # captured from TICS Pro
    70:  0x000E,   # double buffer disabled — changes require R0 write
    69:  0x0011,   # power down system ref output buffer
    68:  0x0020,   # phase sync disabled
    67:  0x1000,
    66:  0x003F,   # JESD registers
    65:  0x0000,
    64:  0x0080,   # system ref divider
    63:  0xC350,   # MASH_RST_COUNT LSBs
    62:  0x0000,   # MASH_RST_COUNT MSBs
    61:  0x03E8,
    60:  0x01F4,
    59:  0x1388,
    58:  0x0000,
    57:  0x0001,   # PFDIN input disabled
    56:  0x0001,
    55:  0x0002,
    54:  0x0000,
    53:  0x0000,
    52:  0x0000,
    51:  0x203F,   # VCO gain (reserved, program default)
    50:  0x0080,   # VCO bias (reserved, program default)
    49:  0x0000,
    48:  0x4180,
    47:  0x0300,
    46:  0x0300,
    45:  0x0000,   # INSTCAL_PLL LSB = 0 (integer-N mode)
    44:  0x0000,   # INSTCAL_PLL MSB = 0 (integer-N mode)
    43:  0x0000,   # NUM LSB = 0 (integer-N mode)
    42:  0x0000,   # NUM MSB = 0 (integer-N mode)
    41:  0x0000,   # MASH_SEED LSB
    40:  0x0000,   # MASH_SEED MSB
    39:  0x0001,   # DEN LSB = 1 (integer-N mode)
    38:  0x0000,   # DEN MSB = 0 (integer-N mode)
    37:  0x0500,
    36:  0x0028,   # PLL_N default
    35:  0x3000,   # MASH_ORDER=0 integer mode, MASH_RESET_N=1
    34:  0x0010,
    33:  0x0000,
    32:  0x1081,   # CHDIV default
    31:  0x0401,
    30:  0xB18C,
    29:  0x318C,
    28:  0x0639,
    27:  0x8001,
    26:  0x0DB0,
    25:  0x0624,
    24:  0x0E34,
    23:  0x1102,
    22:  0xE2BF,
    21:  0x1C64,
    20:  0x272C,
    19:  0x2120,
    18:  0x0000,
    17:  0x15C0,
    16:  0x171C,
    15:  0x2001,
    14:  0x3001,   # pre-R divider = 1
    13:  0x0038,   # post-R divider = 1
    12:  0x0408,   # ref multiplier bypassed
    11:  0x0612,   # ref doubler bypassed
    10:  0x0000,
    9:   0x0005,
    8:   0xC802,
    7:   0x0000,
    6:   0x0A43,
    5:   0x0032,
    4:   0x4204,   # reserved
    3:   0x0041,   # reserved
    2:   0x81F4,   # CLK_DIV
    1:   0x57A0,   # InstaCal_2x=0 (normal), other defaults
    0:   0x6470,   # FCAL_EN=0, FCAL_HPFD_ADJ, FCAL_LPFD_ADJ set for 10-25MHz ref
}