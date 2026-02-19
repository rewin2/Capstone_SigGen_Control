# lmx2820.py
#
# LMX2820 device driver (Fractional-N version)
#

import time

from register_map import *
from init_register_values import INIT_REG_VALUES
from write_order import STATIC_REGS, CAL_REGS


class PLLLockError(RuntimeError):
    pass


class LMX2820:
    def __init__(self, spi, gpio):
        self.spi = spi
        self.gpio = gpio
        self.reg_shadow = {}

    # -------------------------------------------------
    # Power control
    # -------------------------------------------------

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
        """
        for reg in STATIC_REGS:
            if reg not in INIT_REG_VALUES:
                raise KeyError(f"No init value defined for R{reg:03d}")

            value = INIT_REG_VALUES[reg]
            self.write_register(reg, value)

        self.rf_enable(False)

    # -------------------------------------------------
    # RF Enable
    # -------------------------------------------------

    def rf_enable(self, enable: bool):
        self.gpio.rf_enable(enable)

    # -------------------------------------------------
    # Low-level register writes
    # -------------------------------------------------

    def write_register(self, reg: int, value: int):
        if not (0 <= value <= 0xFFFFFF):
            raise ValueError(f"Register value out of range: 0x{value:X}")

        self.reg_shadow[reg] = value
        self.spi.write(reg, value)

    def write_field(self, reg: int, mask: int, shift: int, value: int):
        if value < 0:
            raise ValueError("Field value cannot be negative")

        current = self.reg_shadow.get(reg, 0)
        new_value = (current & ~mask) | ((value << shift) & mask)

        self.write_register(reg, new_value)

    # -------------------------------------------------
    # CHDIV encoding
    # -------------------------------------------------

    def encode_chdiv(self, chdiv: int) -> int:
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
    # GPIO Output Routing
    # -------------------------------------------------

    def configure_output_path(self, outa_mux: int):

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
    # PLL Programming (Fractional-N)
    # -------------------------------------------------

    def program_pll(self, N: int, NUM: int, DEN: int, fractional: bool):

        # ---- Integer N ----
        self.write_field(
            PLL_N_LSB_REG,
            PLL_N_LSB_MASK,
            PLL_N_LSB_SHIFT,
            N & 0xFF,
        )

        self.write_field(
            PLL_N_MSB_REG,
            PLL_N_MSB_MASK,
            PLL_N_MSB_SHIFT,
            (N >> 8) & 0xFF,
        )

        # ---- Fractional Numerator ----
        self.write_field(
            PLL_NUM_LSB_REG,
            PLL_NUM_LSB_MASK,
            PLL_NUM_LSB_SHIFT,
            NUM & 0xFFFF,
        )

        self.write_field(
            PLL_NUM_MSB_REG,
            PLL_NUM_MSB_MASK,
            PLL_NUM_MSB_SHIFT,
            (NUM >> 16),
        )

        # ---- Fractional Denominator ----
        self.write_field(
            PLL_DEN_LSB_REG,
            PLL_DEN_LSB_MASK,
            PLL_DEN_LSB_SHIFT,
            DEN & 0xFFFF,
        )

        self.write_field(
            PLL_DEN_MSB_REG,
            PLL_DEN_MSB_MASK,
            PLL_DEN_MSB_SHIFT,
            (DEN >> 16),
        )

        # ---- Fractional Enable ----
        frac_bit = 1 if fractional else 0

        self.write_field(
            PLL_FRAC_EN_REG,
            PLL_FRAC_EN_MASK,
            PLL_FRAC_EN_SHIFT,
            frac_bit,
        )

    # -------------------------------------------------
    # Frequency Programming (Single Authority)
    # -------------------------------------------------

    def apply_frequency_plan(self, plan: dict):

        # 0. RF OFF
        self.rf_enable(False)

        # 1. Program PLL
        self.program_pll(
            N=plan["N"],
            NUM=plan["NUM"],
            DEN=plan["DEN"],
            fractional=plan["fractional"],
        )

        # 2. CHDIV (divider path only)
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

        # 3. OUTA_MUX register
        self.write_field(
            OUTA_MUX_REG,
            OUTA_MUX_MASK,
            OUTA_MUX_SHIFT,
            plan["outa_mux"],
        )

        # 4. GPIO routing
        self.configure_output_path(plan["outa_mux"])

        # 5. Calibration writes
        for reg in CAL_REGS:
            self.spi.write(reg, self.reg_shadow.get(reg, 0))

        # 6. Wait for lock
        LOCK_TIMEOUT_S = 0.1
        LOCK_POLL_INTERVAL_S = 0.001
        elapsed = 0.0

        while not self.gpio.read_lock_detect():
            if elapsed >= LOCK_TIMEOUT_S:
                raise PLLLockError("PLL failed to lock within timeout")
            time.sleep(LOCK_POLL_INTERVAL_S)
            elapsed += LOCK_POLL_INTERVAL_S

        # 7. RF ON
        self.rf_enable(True)
