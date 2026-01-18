# lmx2820.py
#
# LMX2820 device driver
#

import time

from register_map import *
from write_order import (
    STATIC_REGS,
    FREQ_REGS,
    CAL_REGS,
    OUTPUT_REGS,
)

from frequency_plan import compute_frequency_plan_integer_n
from utils import load_register_image_from_text


class PLLLockError(RuntimeError):
    pass


class LMX2820:
    def __init__(self, spi, gpio):
        self.spi = spi
        self.gpio = gpio

        # Shadow register image (R0–R122)
        self.reg_image = [0] * 123

        self.current_plan = None

    # ------------------------------------------------------------
    # Power / Reset
    # ------------------------------------------------------------

    def power_on(self):
        self.gpio.power_enable(True)
        self.gpio.reset_pulse()

    def power_off(self):
        self.rf_enable(False)
        self.gpio.power_enable(False)

    def reset(self):
        self.power_off()

    # ------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------

    def initialize_registers(self):
        """
        Load TI default register image and write static configuration.
        """
        self.reg_image = load_register_image_from_text(
            "data/HexRegisterValuesInitialState.txt",
            num_registers=123,
        )

        self._write_static_registers()

    def _write_static_registers(self):
        """
        Write static configuration registers only.
        """
        for reg in STATIC_REGS:
            self.spi.write(reg, self.reg_image[reg])

    # ------------------------------------------------------------
    # RF Output Control
    # ------------------------------------------------------------

    def rf_enable(self, enable: bool):
        self.reg_image[RFOUTA_EN_REG] = set_field(
            self.reg_image[RFOUTA_EN_REG],
            RFOUTA_EN_MASK,
            RFOUTA_EN_SHIFT,
            1 if enable else 0,
        )
        self.spi.write(RFOUTA_EN_REG, self.reg_image[RFOUTA_EN_REG])
        self.gpio.rf_enable(enable)

    # ------------------------------------------------------------
    # Frequency Planning
    # ------------------------------------------------------------

    def compute_frequency_plan(self, freq_hz: int):
        plan = compute_frequency_plan_integer_n(freq_hz)
        self.current_plan = plan
        return plan

    # ------------------------------------------------------------
    # Frequency Programming (UNCHANGED BEHAVIOR)
    # ------------------------------------------------------------

    def apply_frequency_plan(self, plan: dict):
        """
        Update register image from frequency plan and program PLL.
        """
        self._configure_rf_path(plan)
        self._update_registers_from_plan(plan)
        self._write_frequency_sequence()

    # ------------------------------------------------------------
    # RF Path GPIO Configuration
    # ------------------------------------------------------------

    def _configure_rf_path(self, plan):
        band = plan["band"]

        if band == "1_10":
            self.gpio.set_sp4t(0)
            self.gpio.external_doubler_enable(False)

        elif band == "10_22":
            self.gpio.set_sp4t(1)
            self.gpio.external_doubler_enable(False)

        elif band == "22_32":
            self.gpio.set_sp4t(2)
            self.gpio.external_doubler_enable(True)

        elif band == "32_40":
            self.gpio.set_sp4t(3)
            self.gpio.external_doubler_enable(True)

        else:
            raise ValueError(f"Unknown band: {band}")

    # ------------------------------------------------------------
    # Register Updates (PURE DATA)
    # ------------------------------------------------------------

    def _update_registers_from_plan(self, plan):
        self.reg_image[PLL_N_REG] = set_field(
            self.reg_image[PLL_N_REG],
            PLL_N_MASK,
            PLL_N_SHIFT,
            plan["N"],
        )

        self.reg_image[PLL_NUM_REG] = set_field(
            self.reg_image[PLL_NUM_REG],
            PLL_NUM_MASK,
            PLL_NUM_SHIFT,
            0,
        )

        self.reg_image[PLL_DEN_REG] = set_field(
            self.reg_image[PLL_DEN_REG],
            PLL_DEN_MASK,
            PLL_DEN_SHIFT,
            1,
        )

        self.reg_image[CHDIV_REG] = set_field(
            self.reg_image[CHDIV_REG],
            CHDIV_MASK,
            CHDIV_SHIFT,
            plan["chdiv"],
        )

        self.reg_image[OUTA_MUX_REG] = set_field(
            self.reg_image[OUTA_MUX_REG],
            OUTA_MUX_MASK,
            OUTA_MUX_SHIFT,
            plan["outa_mux"],
        )

        self.reg_image[RFOUTA_PWR_REG] = set_field(
            self.reg_image[RFOUTA_PWR_REG],
            RFOUTA_PWR_MASK,
            RFOUTA_PWR_SHIFT,
            plan.get("power", 0x20),
        )

    # ------------------------------------------------------------
    # Ordered Write + Lock Logic (BEHAVIOR PRESERVED)
    # ------------------------------------------------------------

    def _write_frequency_sequence(self):
        MAX_RETRIES = 3

        # Always disable RF during reprogramming
        self.rf_enable(False)

        # Write frequency-defining registers
        for reg in FREQ_REGS:
            self.spi.write(reg, self.reg_image[reg])

        time.sleep(0.001)

        for attempt in range(1, MAX_RETRIES + 1):
            # Trigger VCO calibration
            for reg in CAL_REGS:
                self.spi.write(reg, self.reg_image[reg])

            time.sleep(0.005)

            if self.wait_for_lock(timeout_ms=50):
                # Enable RF output
                for reg in OUTPUT_REGS:
                    self.spi.write(reg, self.reg_image[reg])
                return

        # If we get here, lock failed
        self.rf_enable(False)
        raise PLLLockError("PLL failed to lock after retries")

    # ------------------------------------------------------------
    # Lock Detect
    # ------------------------------------------------------------

    def wait_for_lock(self, timeout_ms=100):
        for _ in range(timeout_ms):
            if self.is_locked():
                return True
        return False

    def is_locked(self):
        return self.gpio.read_lock_detect()
