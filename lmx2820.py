# lmx2820.py
#
# Device driver for the TI LMX2820
#
# Responsibilities:
# - Own the register image
# - Apply frequency plans safely
# - Enforce PLL write ordering
# - Trigger VCO calibration
# - Verify lock before RF enable
#
# Does NOT:
# - Perform PLL math (frequency_plan.py)
# - Manage system state (fsm.py)
# - Expose user APIs (api.py)


import time

from frequency_plan import compute_frequency_plan_integer_n
from utils import load_register_image_from_text
from register_map import *


class LMX2820:
    def __init__(self, spi, gpio):
        self.spi = spi
        self.gpio = gpio

        # Shadow register image (R0–R122)
        self.reg_image = [0] * 123

        self.current_plan = None

    # ============================================================
    # Power & Reset
    # ============================================================

    def power_on(self):
        self.gpio.power_enable(True)
        self.gpio.reset_pulse()

    def power_off(self):
        self.rf_enable(False)
        self.gpio.power_enable(False)

    def reset(self):
        self.power_off()

    # ============================================================
    # Initialization
    # ============================================================

    def initialize_registers(self):
        """
        Load and write the default TI register image.
        Static configuration only.
        """
        self.reg_image = load_register_image_from_text(
            "data/HexRegisterValues_default.txt",
            num_registers=123
        )
        self._write_static_registers()

    # ============================================================
    # RF Output Control
    # ============================================================

    def rf_enable(self, enable: bool):
        self.reg_image[R_RFOUTA_EN] = set_field(
            self.reg_image[R_RFOUTA_EN],
            RFOUTA_EN_MASK,
            RFOUTA_EN_SHIFT,
            1 if enable else 0
        )

        self.spi.write(R_RFOUTA_EN, self.reg_image[R_RFOUTA_EN])
        self.gpio.rf_enable(enable)

    # ============================================================
    # Frequency Planning
    # ============================================================

    def compute_frequency_plan(self, freq_hz: int):
        self.current_plan = compute_frequency_plan_integer_n(freq_hz)
        return self.current_plan

    # ============================================================
    # Apply Frequency Plan
    # ============================================================

    def apply_frequency_plan(self, plan: dict):
        """
        Apply a frequency plan safely:
        - Configure RF path GPIOs
        - Update register image
        - Program PLL with calibration and lock checking
        """

        self._configure_rf_path(plan)
        self._update_registers_from_plan(plan)
        self._write_frequency_sequence()

    # ============================================================
    # RF Path Configuration (GPIO)
    # ============================================================

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
            raise ValueError(f"Unknown frequency band: {band}")

    # ============================================================
    # Register Image Updates (frequency only)
    # ============================================================

    def _update_registers_from_plan(self, plan):
        """
        Update ONLY frequency-related fields.
        """

        # Integer-N configuration
        self.reg_image[R_PLL_NUM] = set_field(
            self.reg_image[R_PLL_NUM],
            PLL_NUM_MASK,
            PLL_NUM_SHIFT,
            0
        )

        self.reg_image[R_PLL_DEN] = set_field(
            self.reg_image[R_PLL_DEN],
            PLL_DEN_MASK,
            PLL_DEN_SHIFT,
            1
        )

        self.reg_image[R_PLL_N] = set_field(
            self.reg_image[R_PLL_N],
            PLL_N_MASK,
            PLL_N_SHIFT,
            plan["N"]
        )

        # Channel divider
        self.reg_image[R_CHDIV] = set_field(
            self.reg_image[R_CHDIV],
            CHDIV_MASK,
            CHDIV_SHIFT,
            plan["chdiv"]
        )

        # Output mux
        self.reg_image[R_OUTA_MUX] = set_field(
            self.reg_image[R_OUTA_MUX],
            OUTA_MUX_MASK,
            OUTA_MUX_SHIFT,
            plan["outa_mux"]
        )

        # Output power
        self.reg_image[R_RFOUTA_PWR] = set_field(
            self.reg_image[R_RFOUTA_PWR],
            RFOUTA_PWR_MASK,
            RFOUTA_PWR_SHIFT,
            plan.get("power", 0x20)
        )

    # ============================================================
    # PLL Write Ordering (Steps 2–4)
    # ============================================================

    # ----------------------------
    # Register groups
    # ----------------------------

    STATIC_REGS = [
        # Written once via default image
    ]

    FREQ_REGS = [
        R_PLL_NUM,
        R_PLL_DEN,
        R_PLL_N,
        R_CHDIV,
        R_OUTA_MUX,
    ]

    OUTPUT_REGS = [
        R_RFOUTA_PWR,
        R_RFOUTA_EN,
    ]

    # ----------------------------
    # Register write helpers
    # ----------------------------

    def _write_reg_list(self, reg_list):
        for reg in reg_list:
            self.spi.write(reg, self.reg_image[reg])

    def _write_static_registers(self):
        """
        Write full static register image at startup.
        """
        for reg, value in enumerate(self.reg_image):
            self.spi.write(reg, value)

    # ----------------------------
    # Calibration
    # ----------------------------

    def _trigger_vco_calibration(self):
        """
        Pulse the VCO calibration bit.
        """

        # Set calibration bit
        self.reg_image[R_VCO_CAL] = set_field(
            self.reg_image[R_VCO_CAL],
            VCO_CAL_MASK,
            VCO_CAL_SHIFT,
            1
        )
        self.spi.write(R_VCO_CAL, self.reg_image[R_VCO_CAL])

        time.sleep(0.001)

        # Clear calibration bit
        self.reg_image[R_VCO_CAL] = set_field(
            self.reg_image[R_VCO_CAL],
            VCO_CAL_MASK,
            VCO_CAL_SHIFT,
            0
        )
        self.spi.write(R_VCO_CAL, self.reg_image[R_VCO_CAL])

    # ----------------------------
    # Frequency programming sequence
    # ----------------------------

    def _write_frequency_sequence(self):
        """
        Safely reprogram the PLL and enable RF output.
        """

        # Ensure RF is disabled during reprogramming
        self.rf_enable(False)

        # Write frequency-defining registers
        self._write_reg_list(self.FREQ_REGS)

        # Allow divider logic to settle
        time.sleep(0.001)

        # Trigger VCO calibration
        self._trigger_vco_calibration()

        # Allow calibration to complete
        time.sleep(0.005)

        # Verify lock
        if not self.wait_for_lock(timeout_ms=50):
            raise RuntimeError("PLL failed to lock")

        # Enable RF output
        self._write_reg_list(self.OUTPUT_REGS)

    # ============================================================
    # Lock Detection
    # ============================================================

    def is_locked(self):
        return self.gpio.read_lock_detect()

    def wait_for_lock(self, timeout_ms=100):
        for _ in range(timeout_ms):
            if self.is_locked():
                return True
            time.sleep(0.001)
        return False
