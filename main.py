# main.py

import argparse
import sys

from spi.spi_driver import SPIDriver
from lmx2820 import LMX2820
from fsm import RFFSM, RFState
from api import RFAPI


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


def build_system() -> RFAPI:
    spi = SPIDriver()
    lmx = LMX2820(spi)
    fsm = RFFSM(lmx)
    api = RFAPI(fsm)
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

    try:
        if args.reset:
            api.reset()
            print("System reset")

        if args.freq is not None:
            api.set_frequency(args.freq)
            print(f"Frequency set to {args.freq} Hz")

        if args.enable:
            api.enable_output()
            print("RF output enabled")

        if args.disable:
            api.disable_output()
            print("RF output disabled")

        print(f"System state: {api.get_state().name}")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
