# fsm.py

from enum import Enum, auto
from lmx2820.frequency_plan import compute_frequency_plan_integer_n


class RFState(Enum):
    POWER_OFF = auto()
    RESET = auto()
    IDLE = auto()
    CALCULATE = auto()
    CONFIGURE_HW = auto()
    PROGRAM_PLL = auto()
    RUNNING = auto()
    ERROR = auto()


class LMX2820FSM:
    def __init__(self, device):
        self.device = device
        self.state = RFState.POWER_OFF
        self.current_plan = Non# fsm.py
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
e

    # --------------------------------------------------
    # Power & reset control
    # --------------------------------------------------

    def power_on(self):
        if self.state != RFState.POWER_OFF:
            raise RuntimeError("Already powered on")

        self.device.power_on()
        self.state = RFState.RESET

        self.device.load_default_register_image()
        self.device.rf_disable()

        self.state = RFState.IDLE

    def power_off(self):
        self.device.rf_disable()
        self.device.power_off()
        self.state = RFState.POWER_OFF

    def reset(self):
        self.device.rf_disable()
        self.device.reset_device()
        self.device.load_default_register_image()
        self.state = RFState.IDLE

    # --------------------------------------------------
    # Frequency control
    # --------------------------------------------------

    def set_frequency(self, freq_ghz):
        if self.state not in (RFState.IDLE, RFState.RUNNING):
            raise RuntimeError("Cannot set frequency in current state")

        try:
            # ---------------------------
            # CALCULATE
            # ---------------------------
            self.state = RFState.CALCULATE
            plan = compute_frequency_plan_integer_n(freq_ghz)
            self.current_plan = plan

            # ---------------------------
            # CONFIGURE HARDWARE
            # ---------------------------
            self.state = RFState.CONFIGURE_HW
            self.device.rf_disable()

            # Configure RF switches
            self.device.configure_sp4t_switch(plan.mode)

            # Configure external doubler path if needed
            if self.device.external_doubler_required(plan.mode):
                self.device.configure_external_doubler(True)
            else:
                self.device.configure_external_doubler(False)

            # ---------------------------
            # PROGRAM PLL
            # ---------------------------
            self.state = RFState.PROGRAM_PLL
            self.device.apply_frequency_plan(plan)
            self.device.trigger_calibration()

            if not self.device.wait_for_lock():
                raise RuntimeError("PLL failed to lock")

            # ---------------------------
            # RUNNING
            # ---------------------------
            self.device.rf_enable()
            self.state = RFState.RUNNING

        except Exception as e:
            self._enter_error_state(str(e))

    # --------------------------------------------------
    # Error handling
    # --------------------------------------------------

    def _enter_error_state(self, reason):
        self.device.rf_disable()
        self.device.log_error(reason)
        self.state = RFState.ERROR

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def get_status(self):
        return {
            "state": self.state.name,
            "frequency_ghz": (
                self.current_plan.freq_ghz
                if self.current_plan else None
            ),
            "mode": (
                self.current_plan.mode
                if self.current_plan else None
            )
        }
