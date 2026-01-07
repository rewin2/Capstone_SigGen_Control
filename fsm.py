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
        self.current_plan = None

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
