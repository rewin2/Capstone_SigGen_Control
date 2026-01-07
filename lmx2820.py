# lmx2820.py
#
# LMX2820 device abstraction
#
# Responsibilities:
# - Own register image
# - Load default register image
# - Translate frequency plans into register writes
# - Control RF enable/disable
# - Control calibration & lock
# - Control RF switch paths (SP4T, external doubler)
#
# Does NOT:
# - Decide sequencing (FSM does)
# - Do frequency math (planner does)


import time


class LMX2820:
    NUM_REGISTERS = 123

    def __init__(self, spi, gpio=None):
        """
        spi  : SPI interface object (must provide write())
        gpio : Optional GPIO interface for switches, enables, etc.
        """
        self.spi = spi
        self.gpio = gpio

        # Software mirror of hardware registers
        self.reg_image = [0] * self.NUM_REGISTERS

        # Cached status
        self.rf_enabled = False

    # --------------------------------------------------
    # Power / reset
    # --------------------------------------------------

    def power_on(self):
        # Optional: enable power rails, clocks, etc.
        if self.gpio:
            self.gpio.power_enable(True)

    def power_off(self):
        self.rf_disable()
        if self.gpio:
            self.gpio.power_enable(False)

    def reset_device(self):
        # Optional hardware reset pin
        if self.gpio:
            self.gpio.reset_pulse()
        time.sleep(0.01)

    # --------------------------------------------------
    # Register image handling
    # --------------------------------------------------

    def load_default_register_image(self, path="data/HexRegisterValues_default.txt"):
        from lmx2820.utils import load_register_image_from_text
        self.reg_image = load_register_image_from_text(path)

    def write_reg(self, reg, value):
        """
        Write a single register to hardware.
        """
        self.spi.write(reg, value & 0xFFFFFF)

    def write_register_image(self, regs=None):
        """
        Write all or selected registers to hardware.
        """
        if regs is None:
            regs = range(self.NUM_REGISTERS)

        for r in regs:
            self.write_reg(r, self.reg_image[r])

    # --------------------------------------------------
    # RF control
    # --------------------------------------------------

    def rf_enable(self):
        # Example: OUTA_EN bit in R78
        self.reg_image[78] |= (1 << 2)
        self.write_reg(78, self.reg_image[78])
        self.rf_enabled = True

    def rf_disable(self):
        self.reg_image[78] &= ~(1 << 2)
        self.write_reg(78, self.reg_image[78])
        self.rf_enabled = False

    # --------------------------------------------------
    # Frequency plan application
    # --------------------------------------------------

    def apply_frequency_plan(self, plan):
        """
        Apply PLL-related values from a FrequencyPlan.
        """

        touched = set()

        # PLL_N (R36)
        self.reg_image[36] = plan.pll_n
        touched.add(36)

        # PLL_NUM (R42:R43)
        self.reg_image[42] = (plan.pll_num >> 8) & 0xFF
        self.reg_image[43] = plan.pll_num & 0xFF
        touched.update({42, 43})

        # PLL_DEN (R38:R39)
        self.reg_image[38] = (plan.pll_den >> 8) & 0xFF
        self.reg_image[39] = plan.pll_den & 0xFF
        touched.update({38, 39})

        # CHDIV (R75:R76)
        self.reg_image[75] = (plan.chdiv >> 8) & 0xFF
        self.reg_image[76] = plan.chdiv & 0xFF
        touched.update({75, 76})

        # OUTA_MUX (R78 bits [1:0])
        self.reg_image[78] &= ~0b11
        self.reg_image[78] |= (plan.outa_mux & 0b11)
        touched.add(78)

        # Write changed registers
        for r in sorted(touched):
            self.write_reg(r, self.reg_image[r])

    # --------------------------------------------------
    # Calibration / lock
    # --------------------------------------------------

    def trigger_calibration(self):
        # FCAL_EN bit example (R0 bit 4)
        self.reg_image[0] |= (1 << 4)
        self.write_reg(0, self.reg_image[0])

    def wait_for_lock(self, timeout_s=0.1):
        """
        Wait for PLL lock.
        Returns True if locked, False on timeout.
        """
        start = time.time()
        while time.time() - start < timeout_s:
            if self.read_lock_status():
                return True
            time.sleep(0.001)
        return False

    def read_lock_status(self):
        """
        Stub: return True if PLL is locked.
        Replace with real lock-detect read if available.
        """
        return True

    # --------------------------------------------------
    # RF switch control
    # --------------------------------------------------

    def configure_sp4t_switch(self, mode):
        """
        Configure SP4T RF switch for band selection.
        """
        if not self.gpio:
            return

        # Example mapping
        if mode == 1:
            self.gpio.set_sp4t(0)
        elif mode == 2:
            self.gpio.set_sp4t(1)
        elif mode == 3:
            self.gpio.set_sp4t(2)
        elif mode == 4:
            self.gpio.set_sp4t(3)

    def external_doubler_required(self, mode):
        """
        External doubler required for selected mode?
        """
        return mode in (3, 4)

    def configure_external_doubler(self, enable):
        if not self.gpio:
            return
        self.gpio.external_doubler_enable(enable)

    # --------------------------------------------------
    # Diagnostics
    # --------------------------------------------------

    def log_error(self, reason):
        print(f"[LMX2820 ERROR] {reason}")
