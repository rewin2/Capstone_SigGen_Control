# gpio.py
#
# GPIO abstraction for LMX2820 system
#
# Responsibilities:
# - RF enable / disable control
# - SP4T RF switch control
# - External doubler enable
# - Optional lock-detect input
#
# Does NOT:
# - Know about registers
# - Know about PLL math
# - Know about FSM logic


class GPIOBase:
    """
    Abstract GPIO interface.
    """

    # ----------------------------
    # Power / reset
    # ----------------------------

    def power_enable(self, enable: bool):
        raise NotImplementedError

    def reset_pulse(self):
        raise NotImplementedError

    # ----------------------------
    # RF control
    # ----------------------------

    def rf_enable(self, enable: bool):
        raise NotImplementedError

    # ----------------------------
    # RF switches
    # ----------------------------

    def set_sp4t(self, position: int):
        """
        Select SP4T RF switch position.
        position: 0–3
        """
        raise NotImplementedError

    def external_doubler_enable(self, enable: bool):
        raise NotImplementedError

    # ----------------------------
    # Status
    # ----------------------------

    def read_lock_detect(self) -> bool:
        """
        Optional PLL lock-detect input.
        """
        raise NotImplementedError

class MockGPIO(GPIOBase):
    """
    Mock GPIO driver for simulation and testing.
    """

    def __init__(self):
        self.powered = False
        self.rf_enabled = False
        self.sp4t_pos = None
        self.external_doubler = False

    # ----------------------------
    # Power / reset
    # ----------------------------

    def power_enable(self, enable: bool):
        self.powered = enable
        print(f"[GPIO MOCK] POWER {'ON' if enable else 'OFF'}")

    def reset_pulse(self):
        print("[GPIO MOCK] RESET pulse")

    # ----------------------------
    # RF control
    # ----------------------------

    def rf_enable(self, enable: bool):
        self.rf_enabled = enable
        print(f"[GPIO MOCK] RF {'ENABLED' if enable else 'DISABLED'}")

    # ----------------------------
    # RF switches
    # ----------------------------

    def set_sp4t(self, position: int):
        if position not in (0, 1, 2, 3):
            raise ValueError("SP4T position must be 0–3")
        self.sp4t_pos = position
        print(f"[GPIO MOCK] SP4T → position {position}")

    def external_doubler_enable(self, enable: bool):
        self.external_doubler = enable
        print(
            f"[GPIO MOCK] External doubler "
            f"{'ENABLED' if enable else 'DISABLED'}"
        )

    # ----------------------------
    # Status
    # ----------------------------

    def read_lock_detect(self) -> bool:
        # Always locked in simulation
        return True

class RealGPIO(GPIOBase):
    """
    Real GPIO driver skeleton.
    Adapt pin numbers and library to your platform.
    """

    def __init__(self, hw):
        """
        hw: platform-specific GPIO backend
        """
        self.hw = hw

        # Example pin assignments
        self.PIN_POWER_EN = 5
        self.PIN_RF_EN = 6
        self.PIN_DBL_EN = 13
        self.PIN_SP4T = (16, 19)   # 2-bit select
        self.PIN_LOCK = 26

        self._configure_pins()

    def _configure_pins(self):
        # Platform-specific pin setup goes here
        pass

    # ----------------------------
    # Power / reset
    # ----------------------------

    def power_enable(self, enable: bool):
        self.hw.write(self.PIN_POWER_EN, enable)

    def reset_pulse(self):
        self.hw.write(self.PIN_RF_EN, False)
        self.hw.delay_ms(10)
        self.hw.write(self.PIN_RF_EN, True)

    # ----------------------------
    # RF control
    # ----------------------------

    def rf_enable(self, enable: bool):
        self.hw.write(self.PIN_RF_EN, enable)

    # ----------------------------
    # RF switches
    # ----------------------------

    def set_sp4t(self, position: int):
        if position not in (0, 1, 2, 3):
            raise ValueError("SP4T position must be 0–3")

        b0 = position & 0x1
        b1 = (position >> 1) & 0x1

        self.hw.write(self.PIN_SP4T[0], b0)
        self.hw.write(self.PIN_SP4T[1], b1)

    def external_doubler_enable(self, enable: bool):
        self.hw.write(self.PIN_DBL_EN, enable)

    # ----------------------------
    # Status
    # ----------------------------

    def read_lock_detect(self) -> bool:
        return bool(self.hw.read(self.PIN_LOCK))
