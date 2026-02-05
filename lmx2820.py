# lmx2820.py
#
# LMX2820 device driver
#

import time

from frequency_plan import compute_frequency_plan_integer_n
from register_map import *
from spi import MockSPI
from utils import load_register_file
from utils import encode_chdiv
from init_register_values import INIT_REG_VALUES
from write_order import (
    STATIC_REGS,
    FREQ_REGS,
    CAL_REGS,
    OUTPUT_REGS,
)


class PLLLockError(RuntimeError):
    pass


class LMX2820:
    def __init__(self, spi, gpio, register_file: str | None = None):
        self.spi = spi
        self.gpio = gpio
        self.register_file ="data/HexRegisterValuesInitialState.txt"
        self.reg_shadow = {}

    def power_on(self):
        self.gpio.power_enable(True)
        self.gpio.reset_pulse()

    def power_off(self):
        self.rf_enable(False)
        self.gpio.power_enable(False)

    def reset(self):
        self.power_off()

    # -------------------------------------------------
    # Initialization
    # -------------------------------------------------

    def initialize_registers(self):
        """
        Write static configuration registers at startup.
        Uses strict write ordering + explicit values.
        """

        for reg in STATIC_REGS:
            if reg not in INIT_REG_VALUES:
                raise KeyError(
                    f"No init value defined for register R{reg:03d}"
                )

            value = INIT_REG_VALUES[reg]
            self.write_register(reg, value)

        self.rf_enable(False)

    # -------------------------------------------------
    # RF enable
    # -------------------------------------------------

    def rf_enable(self, enable: bool):
        self.gpio.rf_enable(enable)

    # -------------------------------------------------
    # Low-level register writes
    # -------------------------------------------------

    def write_register(self, reg: int, value: int):
        """
        Full 24-bit register overwrite.
        """
        if not (0 <= value <= 0xFFFFFF):
            raise ValueError(f"Register value out of range: 0x{value:X}")

        self.reg_shadow[reg] = value
        self.spi.write(reg, value)

    def write_field(self, reg: int, mask: int, shift: int, value: int):
        """
        Write a masked bitfield into a register.
        """
        if value < 0:
            raise ValueError("Field value cannot be negative")

        current = self.reg_shadow.get(reg, 0)
        new_value = (current & ~mask) | ((value << shift) & mask)

        self.reg_shadow[reg] = new_value
        self.spi.write(reg, new_value)

    # -------------------------------------------------
    # CHDIV encoding
    # -------------------------------------------------

    def encode_chdiv(self, chdiv: int) -> int:
        """
        Encode channel divider ratio into register field value.
        """
        encoding = {
            2: 0,
            4: 1,
            8: 2,
            16: 3,
            32: 4,
            64: 5,
            128: 6,
        }

        if chdiv not in encoding:
            raise ValueError(f"Invalid CHDIV value: {chdiv}")

        return encoding[chdiv]

    # -------------------------------------------------
    # GPIO-only output routing
    # -------------------------------------------------

    def configure_output_path(self, outa_mux: int):
        """
        Configure external RF routing only.
        OUTA_MUX register must already be programmed.
        """

        if outa_mux == 0:
            self.gpio.set_sp4t(0)
            self.gpio.external_doubler_enable(False)

        elif outa_mux == 1:
            self.gpio.set_sp4t(1)
            self.gpio.external_doubler_enable(False)

        elif outa_mux == 2:
            self.gpio.set_sp4t(2)
            self.gpio.external_doubler_enable(True)

        else:
            raise ValueError(f"Invalid OUTA_MUX value: {outa_mux}")

    # -------------------------------------------------
    # Frequency programming (SINGLE AUTHORITY)
    # -------------------------------------------------

    def apply_frequency_plan(self, plan: dict):
        """
        Apply a complete frequency plan.
        This is the ONLY function allowed to program
        frequency-related registers.
        """

        # 0. RF OFF
        self.rf_enable(False)

        # 1. PLL N divider
        n = plan["N"]

        self.write_field(
            PLL_N_LSB_REG,
            PLL_N_LSB_MASK,
            PLL_N_LSB_SHIFT,
            n & 0xFF,
        )

        self.write_field(
            PLL_N_MSB_REG,
            PLL_N_MSB_MASK,
            PLL_N_MSB_SHIFT,
            (n >> 8) & 0xFF,
        )

        # 2. CHDIV (ONLY when divider path is used)
        if plan["outa_mux"] == 0:
            if plan["chdiv"] is None:
                raise ValueError("CHDIV required when OUTA_MUX = 0")

            chdiv_code = self.encode_chdiv(plan["chdiv"])

            self.write_field(
                CHDIV_REG,
                CHDIV_MASK,
                CHDIV_SHIFT,
                chdiv_code,
            )

        # 3. OUTA_MUX
        self.write_field(
            OUTA_MUX_REG,
            OUTA_MUX_MASK,
            OUTA_MUX_SHIFT,
            plan["outa_mux"],
        )

        # 4. GPIO routing
        self.configure_output_path(plan["outa_mux"])

        # 5. Calibration / update
        for reg in CAL_REGS:
            self.spi.write(reg, self.reg_shadow.get(reg, 0))

        # 6. RF ON
        self.rf_enable(True)
