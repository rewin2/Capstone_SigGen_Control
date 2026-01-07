# api.py
#
# High-level control API for the LMX2820 signal generator
#
# This is the ONLY interface user code should use.
#
# Responsibilities:
# - Expose safe, high-level commands
# - Hide FSM, PLL, register, SPI, GPIO details
#
# Does NOT:
# - Compute PLL math
# - Touch registers directly
# - Access hardware directly


class SignalGeneratorAPI:
    """
    High-level API for controlling the signal generator.
    """

    def __init__(self, fsm):
        """
        Args:
            fsm: Instance of LMX2820FSM
        """
        self.fsm = fsm

    # ------------------------------------------------------------
    # Lifecycle control
    # ------------------------------------------------------------

    def start(self):
        """
        Power up and initialize the system.
        """
        self.fsm.startup()

    def power_off(self):
        """
        Safely power down the system.
        """
        self.fsm.power_off()

    def reset(self):
        """
        Reset the system from an error state.
        """
        self.fsm.reset()

    # ------------------------------------------------------------
    # RF control
    # ------------------------------------------------------------

    def set_frequency(self, freq_hz: int):
        """
        Set output frequency.

        Args:
            freq_hz (int): Frequency in Hz
        """
        if freq_hz <= 0:
            raise ValueError("Frequency must be positive")

        self.fsm.set_frequency(freq_hz)

    def enable_rf(self):
        """
        Enable RF output.
        """
        self.fsm.enable_rf()

    def disable_rf(self):
        """
        Disable RF output.
        """
        self.fsm.disable_rf()

    # ------------------------------------------------------------
    # Status / query
    # ------------------------------------------------------------

    def get_state(self):
        """
        Get current FSM state.
        """
        return self.fsm.state

    def get_frequency(self):
        """
        Get currently programmed frequency.
        """
        return self.fsm.current_frequency

    def is_locked(self) -> bool:
        """
        Query PLL lock status.
        """
        return self.fsm.is_locked()
