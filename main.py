# main.py

import argparse
import sys
import traceback

from spi import MockSPI
from lmx2820 import LMX2820
from fsm import RFFSM, RFState
from api import SignalGeneratorAPI
from gpio import MockGPIO


def parse_frequency(freq_str: str) -> int:
    """
    Parse frequency strings like:
      15e9
      15000000000
      15_000_000_000
    """
    try:
        return int(float(freq_str))
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid frequency value: {freq_str}"
        )


def build_system() -> SignalGeneratorAPI:
    spi = MockSPI()
    gpio = MockGPIO()
    lmx = LMX2820(spi, gpio)
    fsm = RFFSM(lmx)
    api = SignalGeneratorAPI(fsm)
    return api


def main():
    parser = argparse.ArgumentParser(
        description="LMX2820 RF Signal Generator CLI"
    )

    parser.add_argument(
        "--freq",
        type=parse_frequency,
        help="Set output frequency (e.g. 15e9)"
    )

    parser.add_argument(
        "--enable",
        action="store_true",
        help="Enable RF output"
    )

    parser.add_argument(
        "--disable",
        action="store_true",
        help="Disable RF output"
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset RF system"
    )

    args = parser.parse_args()

    api = build_system()

    api.power_on()


    try:
        if args.reset:
            api.reset()
            print("System reset")

        if args.freq is not None:
            api.set_frequency(args.freq)
            print(f"Frequency set to {args.freq} Hz")

        if args.enable:
            api.rf_enable()
            print("RF output enabled")

        if args.disable:
            api.rf_disable()
            print("RF output disabled")

        print(f"System state: {api.get_state().name}")

    except Exception as e:
        error_msg = (
            f"{type(e).__name__}: {e}"
            if str(e)
            else f"{type(e).__name__} (no message)")
        
        print("=== EXCEPTION ===")
        print(e)
        print("=== FSM ERROR ===")
        print(api.get_last_error())
        sys.exit(1)

        traceback.print_exc()

if __name__ == "__main__":
    main()
