# main.py
#
# Top-level entry point for LMX2820 signal generator
#
# Responsibilities:
# - Select hardware backend (mock vs real)
# - Instantiate drivers
# - Create PLL device and FSM
# - Provide a simple control flow
#
# Does NOT:
# - Implement PLL math
# - Know register bit meanings
# - Manage GPIO or SPI details


from spi import MockSPI, RealSPI
from gpio import MockGPIO, RealGPIO
from lmx2820 import LMX2820
from fsm import RFFSM


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

USE_MOCK_HARDWARE = True   # Set False for real hardware
DEFAULT_FREQUENCY_HZ = 1_000_000_000  # 1 GHz


# ------------------------------------------------------------
# Hardware setup
# ------------------------------------------------------------

def create_hardware():
    if USE_MOCK_HARDWARE:
        print("[SYSTEM] Using MOCK hardware")
        spi = MockSPI()
        gpio = MockGPIO()
    else:
        print("[SYSTEM] Using REAL hardware")

        # ---- SPI example (platform-specific) ----
        # import spidev
        # spi_dev = spidev.SpiDev()
        # spi_dev.open(0, 0)
        # spi = RealSPI(spi_dev)

        # ---- GPIO example (platform-specific) ----
        # import my_gpio_backend
        # gpio_hw = my_gpio_backend.GPIO()
        # gpio = RealGPIO(gpio_hw)

        raise NotImplementedError(
            "Real hardware backend not configured yet"
        )

    return spi, gpio


# ------------------------------------------------------------
# Main application
# ------------------------------------------------------------

def main():
    # Create hardware drivers
    spi, gpio = create_hardware()

    # Create PLL device
    pll = LMX2820(spi=spi, gpio=gpio)

    # Create FSM
    fsm = RFFSM(pll)

    # ----------------------------
    # Startup sequence
    # ----------------------------
    print("[SYSTEM] Starting up")
    fsm.power_on()

    # ----------------------------
    # Standby (RF off)
    # ----------------------------
    print("[SYSTEM] System in standby (RF disabled)")

    # ----------------------------
    # Set default frequency
    # ----------------------------
    print(f"[SYSTEM] Setting default frequency: {DEFAULT_FREQUENCY_HZ/1e9:.1f} GHz")
    fsm.set_frequency(DEFAULT_FREQUENCY_HZ)

    print("[SYSTEM] RF output active")

    # ----------------------------
    # Example: change frequency
    # ----------------------------
    while True:
        try:
            user_input = input("\nEnter frequency in GHz (or 'q' to quit): ")

            if user_input.lower() in ("q", "quit", "exit"):
                break

            freq_ghz = float(user_input)
            freq_hz = int(freq_ghz * 1e9)

            fsm.set_frequency(freq_hz)

        except Exception as e:
            print(f"[ERROR] {e}")

    # ----------------------------
    # Power-down
    # ----------------------------
    print("[SYSTEM] Powering down")
    fsm.power_off()


if __name__ == "__main__":
    main()
