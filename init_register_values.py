from register_map import *

# Static power-up values (datasheet / TI tool derived)
INIT_REG_VALUES = {
    SYS_CTRL_REG:     0x6471,
    SYS_PWR_REG:      0x57A0,
    SYS_RESET_REG:    0x81F4,
    REF_CTRL_REG:     0x0000,
    REF_DIV_REG:      0x0612,
    VCO_BIAS_REG:     0x0080,
    VCO_GAIN_REG:     0x203F,
    RFOUTA_EN_REG:    0x0000,
}
