# lmx2820.py
#
# Device driver for TI LMX2820
#
# Responsibilities:
# - Own register image
# - Apply frequency plans safely
# - Control GPIO RF paths
# - Write registers via SPI
#
# Does NOT:
# - Know FSM states
# - Accept user input
# - Perform sequencing decisions


from frequency_plan import compute_frequency_plan_integer_n
from utils import load_register_image_from_text
from register_map import *


class LMX2820:
    def __init__(self, spi, gpio):
        self.spi = spi
        self.gpio = gpio

        # Shadow register image (R0–R122)
        self.reg_image = [0] * 123

        # Cached plan
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
        self.reg_image = load_register_image_from_text(
            "data/HexRegisterValues_default.txt",
            num_registers=123
        )
        self._write_register_image()

    # ------------------------------------------------------------
    # RF Control
    # ------------------------------------------------------------

    def rf_enable(self, enable: bool):
        self.reg_image[R_RFOUTA_EN] = set_field(
            self.reg_image[R_RFOUTA_EN],
            RFOUTA_EN_MASK,
            RFOUTA_EN_SHIFT,
            1 if enable else 0
        )
        self.spi.write(R_RFOUTA_EN, self.reg_image[R_RFOUTA_EN])
        self.gpio.rf_enable(enable)

    # ------------------------------------------------------------
    # Frequency Planning
    # ------------------------------------------------------------

    def compute_frequency_plan(self, freq_hz: int):
        plan = compute_frequency_plan_integer_n(freq_hz)
        self.current_plan = plan
        return plan

    # ------------------------------------------------------------
    # Apply Frequency Plan
    # ------------------------------------------------------------

    def apply_frequency_plan(self, plan: dict):
        """
        Apply a computed frequency plan:
        - Configure RF switches
        - Update register image
        - Write registers
        """

        self._configure_rf_path(plan)
        self._update_registers_from_plan(plan)
        self._write_register_image()

    # ------------------------------------------------------------
    # RF Path Configuration
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
            raise ValueError(f"Unknown frequency band: {band}")

    # ------------------------------------------------------------
    # Register Updates (SAFE)
    # ------------------------------------------------------------

    def _update_registers_from_plan(self, plan):
        """
        Update only the required bitfields based on the frequency plan.
        """

        # PLL N
        self.reg_image[R_PLL_N] = set_field(
            self.reg_image[R_PLL_N],
            PLL_N_MASK,
            PLL_N_SHIFT,
            plan["N"]
        )

        # Integer-N mode → NUM = 0, DEN = 1
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

        # Channel Divider
        self.reg_image[R_CHDIV] = set_field(
            self.reg_image[R_CHDIV],
            CHDIV_MASK,
            CHDIV_SHIFT,
            plan["chdiv"]
        )

        # Output Mux
        self.reg_image[R_OUTA_MUX] = set_field(
            self.reg_image[R_OUTA_MUX],
            OUTA_MUX_MASK,
            OUTA_MUX_SHIFT,
            plan["outa_mux"]
        )

        # Output Power
        self.reg_image[R_RFOUTA_PWR] = set_field(
            self.reg_image[R_RFOUTA_PWR],
            RFOUTA_PWR_MASK,
            RFOUTA_PWR_SHIFT,
            plan.get("power", 0x20)
        )

    # ------------------------------------------------------------
    # SPI Write Logic
    # ------------------------------------------------------------

    def _write_register_image(self):
        """
        Write entire register image to hardware.
        """
        for reg, value in enumerate(self.reg_image):
            self.spi.write(reg, value)

    # ------------------------------------------------------------
    # Lock Detection
    # ------------------------------------------------------------

    def wait_for_lock(self, timeout_ms=100):
        for _ in range(timeout_ms):
            if self.is_locked():
                return True
        return False

    def is_locked(self):
        return self.gpio.read_lock_detect()
