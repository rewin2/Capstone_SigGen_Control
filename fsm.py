# fsm.py
#
# Finite State Machine for RF Signal Generator
#
# Responsibilities:
# - Manage system state
# - Enforce legal transitions
# - Gate user commands
# - Escalate hardware errors
#
# Does NOT:
# - Perform PLL math
# - Touch registers
# - Control GPIO timing
# - Retry hardware actions


from enum import Enum, auto
from lmx2820 import PLLLockError


class RFState(Enum):
    POWER_OFF = auto()
    STANDBY = auto()      # Powered, RF disabled, no frequency set
    READY = auto()        # Locked, RF enabled
    ERROR = auto()        # Fatal error, reset-only exit


class RFFSM:
    def __init__(self, device):
        """
        device: instance of LMX2820
        """
        self.device = device
        self.state = RFState.POWER_OFF
        self.current_freq_hz = None

    # ============================================================
    # Power Control
    # ============================================================

    def power_on(self):
        if self.state != RFState.POWER_OFF:
            return

        self.device.power_on()
        self.device.initialize_registers()

        # Ensure RF is disabled on entry
        self.device.rf_enable(False)

        self.state = RFState.STANDBY

    def power_off(self):
        self.device.power_off()
        self.state = RFState.POWER_OFF
        self.current_freq_hz = None

    def reset(self):
        """
        Reset is the ONLY exit from ERROR.
        """
        self.device.power_off()
        self.device.power_on()
        self.device.initialize_registers()
        self.device.rf_enable(False)

        self.state = RFState.STANDBY
        self.current_freq_hz = None

    # ============================================================
    # Frequency Control
    # ============================================================

    def set_frequency(self, freq_hz: int):
        """
        Set output frequency in Hz.
        Legal only in STANDBY or READY.
        """

        if self.state == RFState.ERROR:
            raise RuntimeError("Device in ERROR state. Reset required.")

        if self.state not in (RFState.STANDBY, RFState.READY):
            raise RuntimeError(f"Cannot set frequency in state {self.state}")

        try:
            # Compute plan (pure math)
            plan = self.device.compute_frequency_plan(freq_hz)

            # Apply plan (hardware sequencing handled by driver)
            self.device.apply_frequency_plan(plan)

            self.current_freq_hz = freq_hz
            self.state = RFState.READY

        except PLLLockError as e:
            self._enter_error_state(str(e))

        except Exception as e:
            # Any unexpected error is fatal
            self._enter_error_state(f"Unexpected error: {e}")

    # ============================================================
    # RF Control
    # ============================================================

    def disable_rf(self):
        """
        Explicitly disable RF output without powering down.
        """
        if self.state == RFState.READY:
            self.device.rf_enable(False)
            self.state = RFState.STANDBY

    # ============================================================
    # Error Handling
    # ============================================================

    def _enter_error_state(self, reason: str):
        self.device.rf_enable(False)
        self.device.log_error(reason)
        self.state = RFState.ERROR

    # ============================================================
    # Status
    # ============================================================

    def get_state(self) -> RFState:
        return self.state

    def is_rf_active(self) -> bool:
        return self.state == RFState.READY
