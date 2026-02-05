from register_map import *

# Static power-up values (datasheet / TI tool derived)
INIT_REG_VALUES = {
    SYS_CTRL_REG:     0x006471,
    SYS_PWR_REG:      0x0157A0,
    SYS_RESET_REG:    0x0281F4,
    REF_CTRL_REG:     0x0A0000,
    REF_DIV_REG:      0x0B0612,
    VCO_BIAS_REG:     0x320080,
    VCO_GAIN_REG:     0x33203F,
    RFOUTA_EN_REG:    0x470000,
}
