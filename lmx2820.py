# lmx2820.py
#
# LMX2820 device driver (Fractional-N version)
#

import time

from register_map import *
from init_register_values import INIT_REG_VALUES
from write_order import STATIC_REGS, CAL_REGS, FREQ_REGS


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
        for reg in STATIC_REGS:
            if reg not in INIT_REG_VALUES:
                raise KeyError(f"No init value defined for R{reg:03d}")

            value = INIT_REG_VALUES[reg]

            if reg == SYS_CTRL_REG:
                value = value & ~FCAL_EN_MASK

            self.write_register(reg, value)

        time.sleep(0.010) 

        r0_cal = INIT_REG_VALUES[SYS_CTRL_REG] | FCAL_EN_MASK
        self.write_register(SYS_CTRL_REG, r0_cal)

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
        if not (0 <= value <= 0xFFFF):
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

    def configure_output_path(self, plan: dict):
        """
        Configure GPIO routing based on frequency band.

        Band mapping → SP4T position:
            "1_10"  → position 0  (divider or direct VCO, no doubler)
            "10_22" → position 1  (direct VCO or internal doubler)
            "22_30" → position 2  (internal + external doubler)
            "30_40" → position 3  (internal + external doubler)

        External doubler is driven by the plan, not inferred from band.
        """
        band = plan["band"]
        external_doubler = plan.get("external_doubler", False)

        if band == "1_10":
            self.gpio.set_sp4t(0)
            self.gpio.external_doubler_enable(False)

        elif band == "10_22":
            self.gpio.set_sp4t(1)
            self.gpio.external_doubler_enable(False)

        elif band == "22_30":
            self.gpio.set_sp4t(2)
            self.gpio.external_doubler_enable(True)

        elif band == "30_40":
            self.gpio.set_sp4t(3)
            self.gpio.external_doubler_enable(True)

        else:
            raise ValueError(f"Unknown band: '{band}'")

        if external_doubler != (band in ("22_30", "30_40")):
            raise ValueError(
                f"external_doubler flag inconsistent with band '{band}'"
            )

    # -------------------------------------------------
    # PLL Programming (Fractional-N)
    # -------------------------------------------------

    def program_pll(self, N: int):
        """
        Program integer-N divider only.
        MASH order is set to 0 (integer mode).
        """
        self.write_field(
            PLL_N_REG,
            PLL_N_MASK,
            PLL_N_SHIFT,
            N & 0x7FFF,
        )

        self.write_field(
            MASH_CTRL_REG,
            MASH_ORDER_MASK,
            MASH_ORDER_SHIFT,
            MASH_INTEGER,
        )


    # -------------------------------------------------
    # Frequency Programming (Single Authority)
    # -------------------------------------------------

    def apply_frequency_plan(self, plan: dict):

        # 0. RF OFF
        self.rf_enable(False)

        # 1. GPIO routing first — switch must be in correct position
        #    before RF is enabled
        self.configure_output_path(plan)

        # 2. Program PLL N
        self.program_pll(N=plan["N"])

        # 3. CHDIV (divider path only)
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

        # 4. OUTA_MUX
        self.write_field(
            OUTA_MUX_REG,
            OUTA_MUX_MASK,
            OUTA_MUX_SHIFT,
            plan["outa_mux"],
        )

        # 5. Trigger VCO calibration
        for reg in CAL_REGS:
            self.spi.write(reg, self.reg_shadow.get(reg, 0))

        # 6. Wait for lock
        LOCK_CONFIRM_COUNT   = 3
        LOCK_TIMEOUT_S       = 0.1
        LOCK_POLL_INTERVAL_S = 0.001

        elapsed       = 0.0
        confirm_count = 0

        while confirm_count < LOCK_CONFIRM_COUNT:
            if self.gpio.read_lock_detect():
                confirm_count += 1
            else:
                confirm_count = 0   # reset on any unlock glitch

            if elapsed >= LOCK_TIMEOUT_S:
                raise PLLLockError("PLL failed to lock within timeout")

            time.sleep(LOCK_POLL_INTERVAL_S)
            elapsed += LOCK_POLL_INTERVAL_S

        # 7. RF ON
        self.rf_enable(True)
