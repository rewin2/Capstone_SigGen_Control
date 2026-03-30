"""
SPI Bus Functionality Test Suite  —  LED-Observable Edition
============================================================
Tests an SPI bus using the spidev library (Linux/Raspberry Pi).

This version deliberately paces transfers so that activity on each pin
(MOSI, MISO, SCLK, CS) is visible on LEDs connected to the SPI header.
Every bit pattern that exercises all four pins is sent individually,
with a configurable inter-byte pause between transfers.

SPI pins exercised
------------------
  SCLK  — toggles on every bit of every transfer
  MOSI  — driven by each byte sent
  MISO  — driven by the loopback echo (wire MISO → MOSI)
  CS    — pulled LOW at the start of each xfer, HIGH at the end

Pin coverage guarantee
----------------------
  Walking-ones  : each of the 8 MOSI data lines sees a HIGH for one bit
  Walking-zeros : each bit is LOW while the rest are HIGH
  CS pulse      : each transfer is sent individually → one CS toggle per byte
  SCLK          : 8 clocks per byte regardless of data content

Run with:
    sudo python3 spi_test.py

Requirements:
    pip install spidev
    Enable SPI on Raspberry Pi via raspi-config or /boot/config.txt

Usage:
    sudo python3 spi_test.py [--bus 0] [--device 0] [--speed 50000]
                             [--pause 0.3] [--byte-pause 0.15] [--no-sweep]
"""

import spidev
import time
import argparse
import sys
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class SPIConfig:
    bus: int = 0
    device: int = 0
    # 50 kHz is slow enough that activity is clearly visible on LEDs.
    # Increase to 1_000_000 for production speed testing.
    max_speed_hz: int = 50_000
    mode: int = 0
    bits_per_word: int = 8
    lsbfirst: bool = False
    # Pause between individual bytes (seconds) — makes each CS toggle visible.
    byte_pause: float = 0.15
    # Pause between named test groups (seconds).
    test_pause: float = 0.3
    # Skip the 256-byte full sweep (saves ~40 s at default byte_pause).
    no_sweep: bool = False


# ──────────────────────────────────────────────────────────────────────────────
# Result tracking
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class TestResult:
    name: str
    passed: bool
    details: str = ""
    duration_ms: float = 0.0


@dataclass
class TestSuite:
    results: List[TestResult] = field(default_factory=list)

    def record(self, result: TestResult):
        self.results.append(result)
        status = "PASS" if result.passed else "FAIL"
        log.info(f"  [{status}] {result.name} ({result.duration_ms:.1f} ms) — {result.details}")

    def summary(self):
        passed = sum(1 for r in self.results if r.passed)
        total  = len(self.results)
        log.info("")
        log.info("=" * 60)
        log.info(f"  RESULTS: {passed}/{total} tests passed")
        for r in self.results:
            mark = "✓" if r.passed else "✗"
            log.info(f"  {mark} {r.name}")
        log.info("=" * 60)
        return passed == total


# ──────────────────────────────────────────────────────────────────────────────
# Transfer helpers
# ──────────────────────────────────────────────────────────────────────────────

def xfer_byte(spi: spidev.SpiDev, byte: int, pause: float) -> int:
    """
    Send a single byte and return the echoed response.
    Each call produces exactly one CS low→high transition, 8 SCLK pulses,
    and drives MOSI with the bit pattern of `byte`.
    The inter-call `pause` keeps each pulse visible on an LED.
    """
    response = spi.xfer2([byte])
    time.sleep(pause)
    return response[0]


def xfer_bytes_individually(
    spi: spidev.SpiDev,
    payload: List[int],
    pause: float,
) -> tuple[List[int], float]:
    """
    Send each byte as a separate transaction so that CS toggles once per byte.
    Returns (response_list, total_elapsed_ms).
    """
    responses = []
    t0 = time.perf_counter()
    for byte in payload:
        responses.append(xfer_byte(spi, byte, pause))
    elapsed = (time.perf_counter() - t0) * 1000
    return responses, elapsed


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_open_device(cfg: SPIConfig, suite: TestSuite) -> Optional[spidev.SpiDev]:
    """Open the SPI device and apply configuration."""
    start = time.perf_counter()
    try:
        spi = spidev.SpiDev()
        spi.open(cfg.bus, cfg.device)
        spi.max_speed_hz = cfg.max_speed_hz
        spi.mode = cfg.mode
        spi.bits_per_word = cfg.bits_per_word
        spi.lsbfirst = cfg.lsbfirst
        elapsed = (time.perf_counter() - start) * 1000
        suite.record(TestResult(
            name="Open device",
            passed=True,
            details=(
                f"/dev/spidev{cfg.bus}.{cfg.device} "
                f"@ {cfg.max_speed_hz / 1e3:.1f} kHz  mode={cfg.mode}  "
                f"byte-pause={cfg.byte_pause * 1000:.0f} ms"
            ),
            duration_ms=elapsed,
        ))
        return spi
    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        suite.record(TestResult(
            name="Open device", passed=False,
            details=str(exc), duration_ms=elapsed,
        ))
        return None


# ── Pin-coverage tests ────────────────────────────────────────────────────────

def test_walking_ones_mosi(spi: spidev.SpiDev, suite: TestSuite, pause: float):
    """
    Walking-ones: sends 0x01, 0x02, 0x04 … 0x80 one byte at a time.

    Pin visibility:
      MOSI — single HIGH bit marching LSB→MSB across 8 transfers
      SCLK — 8 pulses per byte (64 total)
      CS   — 8 separate LOW pulses, one per byte
    """
    log.info("    Walking-ones: 0x01 → 0x80 (8 individual transfers)")
    payload = [1 << i for i in range(8)]
    responses, elapsed = xfer_bytes_individually(spi, payload, pause)
    passed = responses == payload
    suite.record(TestResult(
        name="Walking-ones MOSI (0x01 → 0x80)",
        passed=passed,
        details=f"sent={[hex(b) for b in payload]}  recv={[hex(b) for b in responses]}",
        duration_ms=elapsed,
    ))


def test_walking_zeros_mosi(spi: spidev.SpiDev, suite: TestSuite, pause: float):
    """
    Walking-zeros: sends 0xFE, 0xFD, 0xFB … 0x7F one byte at a time.

    Pin visibility:
      MOSI — single LOW bit marching LSB→MSB, all others HIGH
      SCLK — 8 pulses per byte
      CS   — 8 separate pulses
    """
    log.info("    Walking-zeros: 0xFE → 0x7F (8 individual transfers)")
    payload = [0xFF ^ (1 << i) for i in range(8)]
    responses, elapsed = xfer_bytes_individually(spi, payload, pause)
    passed = responses == payload
    suite.record(TestResult(
        name="Walking-zeros MOSI (0xFE → 0x7F)",
        passed=passed,
        details=f"sent={[hex(b) for b in payload]}  recv={[hex(b) for b in responses]}",
        duration_ms=elapsed,
    ))


def test_cs_pulse(spi: spidev.SpiDev, suite: TestSuite, pause: float, count: int = 8):
    """
    Send `count` identical bytes individually to produce `count` CS pulses.

    Pin visibility:
      CS   — `count` clearly separated LOW pulses
      SCLK — 8 pulses per CS assertion
      MOSI/MISO — constant 0xA5 pattern throughout
    """
    log.info(f"    CS pulse: {count} × 0xA5 individual transfers")
    payload = [0xA5] * count
    responses, elapsed = xfer_bytes_individually(spi, payload, pause)
    passed = responses == payload
    suite.record(TestResult(
        name=f"CS toggle ({count} pulses)",
        passed=passed,
        details=f"{count} CS pulses, loopback {'OK' if passed else 'FAIL'}",
        duration_ms=elapsed,
    ))


def test_sclk_burst(spi: spidev.SpiDev, suite: TestSuite, pause: float, count: int = 8):
    """
    Send `count` 0xFF bytes individually to maximise SCLK visibility.

    Pin visibility:
      SCLK — clock bursts with MOSI held HIGH (maximum LED brightness)
      MOSI — held HIGH throughout
      CS   — `count` separate pulses
    """
    log.info(f"    SCLK burst: {count} × 0xFF individual transfers")
    payload = [0xFF] * count
    responses, elapsed = xfer_bytes_individually(spi, payload, pause)
    passed = responses == payload
    suite.record(TestResult(
        name=f"SCLK burst ({count} × 0xFF)",
        passed=passed,
        details=f"received={'OK' if passed else [hex(b) for b in responses]}",
        duration_ms=elapsed,
    ))


def test_alternating_bits(spi: spidev.SpiDev, suite: TestSuite, pause: float):
    """
    Alternating 0xAA / 0x55 patterns — every bit position sees both states.

    Pin visibility:
      MOSI — rapid HIGH/LOW toggle on every clock edge
    """
    for pattern, label in [(0xAA, "10101010"), (0x55, "01010101")]:
        log.info(f"    Alternating bits: 0x{pattern:02X} ({label}), 4 transfers")
        payload = [pattern] * 4
        responses, elapsed = xfer_bytes_individually(spi, payload, pause)
        passed = responses == payload
        suite.record(TestResult(
            name=f"Alternating bits 0x{pattern:02X} ({label})",
            passed=passed,
            details=f"recv={[hex(b) for b in responses]}",
            duration_ms=elapsed,
        ))


def test_all_zeros(spi: spidev.SpiDev, suite: TestSuite, pause: float):
    """All-zero bytes — MOSI held LOW while SCLK and CS remain active."""
    log.info("    All-zeros: 0x00 × 4 transfers")
    payload = [0x00] * 4
    responses, elapsed = xfer_bytes_individually(spi, payload, pause)
    passed = responses == payload
    suite.record(TestResult(
        name="All-zeros (0x00)",
        passed=passed,
        details=f"recv={responses}",
        duration_ms=elapsed,
    ))


def test_all_ones(spi: spidev.SpiDev, suite: TestSuite, pause: float):
    """All-ones bytes — MOSI held HIGH throughout."""
    log.info("    All-ones: 0xFF × 4 transfers")
    payload = [0xFF] * 4
    responses, elapsed = xfer_bytes_individually(spi, payload, pause)
    passed = responses == payload
    suite.record(TestResult(
        name="All-ones (0xFF)",
        passed=passed,
        details=f"recv={[hex(b) for b in responses]}",
        duration_ms=elapsed,
    ))


def test_multi_byte_loopback(spi: spidev.SpiDev, suite: TestSuite, pause: float):
    """Varied mix: 0x00, 0xFF, 0xAA, 0x55, 0x01, 0xFE, 0x7F, 0x80."""
    payload = [0x00, 0xFF, 0xAA, 0x55, 0x01, 0xFE, 0x7F, 0x80]
    log.info(f"    Multi-byte pattern: {[hex(b) for b in payload]}")
    responses, elapsed = xfer_bytes_individually(spi, payload, pause)
    passed = responses == payload
    suite.record(TestResult(
        name="Multi-byte pattern loopback",
        passed=passed,
        details=f"sent={[hex(b) for b in payload]}  recv={[hex(b) for b in responses]}",
        duration_ms=elapsed,
    ))


def test_full_byte_sweep(spi: spidev.SpiDev, suite: TestSuite, pause: float):
    """
    Send every byte value 0x00–0xFF in sequence (256 individual transfers).

    Pin visibility:
      MOSI — every possible 8-bit pattern is driven at least once,
              guaranteeing every bit position sees both 0 and 1.

    Approximate duration: 256 × byte_pause seconds
    (≈ 38 s at the default 0.15 s pause).
    """
    log.info("    Full byte sweep: 0x00 → 0xFF (256 transfers) — be patient!")
    errors = 0
    t0 = time.perf_counter()
    for value in range(256):
        got = xfer_byte(spi, value, pause)
        if got != value:
            errors += 1
            log.warning(f"      Mismatch at 0x{value:02X}: got 0x{got:02X}")
    elapsed = (time.perf_counter() - t0) * 1000
    suite.record(TestResult(
        name="Full byte sweep (0x00–0xFF)",
        passed=(errors == 0),
        details=f"256 values, {errors} mismatch(es)",
        duration_ms=elapsed,
    ))


# ── Configuration / speed tests ───────────────────────────────────────────────

def test_spi_modes(spi: spidev.SpiDev, suite: TestSuite, pause: float):
    """Test all four CPOL/CPHA mode combinations."""
    payload = [0xA5, 0x5A]
    all_passed = True
    for mode in range(4):
        spi.mode = mode
        try:
            responses, elapsed = xfer_bytes_individually(spi, payload, pause)
            ok = responses == payload
            if not ok:
                all_passed = False
            log.info(f"    Mode {mode}: {'OK' if ok else 'FAIL'} (got {[hex(b) for b in responses]})")
        except Exception as exc:
            all_passed = False
            log.warning(f"    Mode {mode}: exception — {exc}")
    suite.record(TestResult(
        name="All four SPI modes (0–3)",
        passed=all_passed,
        details="loopback at each CPOL/CPHA combination",
        duration_ms=0,
    ))


def test_speed_modes(spi: spidev.SpiDev, suite: TestSuite, pause: float):
    """Verify the bus works at several common speeds."""
    speeds = [10_000, 50_000, 100_000, 500_000, 1_000_000]
    payload = [0xA5, 0x5A]
    all_passed = True
    for speed in speeds:
        spi.max_speed_hz = speed
        responses, elapsed = xfer_bytes_individually(spi, payload, pause)
        ok = responses == payload
        if not ok:
            all_passed = False
        log.info(f"    {speed // 1000:>4d} kHz: {'OK' if ok else 'FAIL'} ({elapsed:.1f} ms)")
    suite.record(TestResult(
        name="Multi-speed loopback",
        passed=all_passed,
        details=f"tested {len(speeds)} speeds",
        duration_ms=0,
    ))


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def parse_args() -> SPIConfig:
    parser = argparse.ArgumentParser(
        description="SPI Bus LED-Observable Test Suite",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--bus",        type=int,   default=0,      help="SPI bus number")
    parser.add_argument("--device",     type=int,   default=0,      help="Chip Select index")
    parser.add_argument("--speed",      type=int,   default=50_000, help="Clock speed in Hz")
    parser.add_argument("--mode",       type=int,   default=0,      help="SPI mode 0–3")
    parser.add_argument("--pause",      type=float, default=0.3,    help="Pause between test groups (s)")
    parser.add_argument("--byte-pause", type=float, default=0.15,   help="Pause between individual bytes (s)")
    parser.add_argument("--no-sweep",   action="store_true",        help="Skip the 256-byte full sweep (~38 s)")
    args = parser.parse_args()
    return SPIConfig(
        bus=args.bus,
        device=args.device,
        max_speed_hz=args.speed,
        mode=args.mode,
        byte_pause=args.byte_pause,
        test_pause=args.pause,
        no_sweep=args.no_sweep,
    )


def main():
    cfg = parse_args()
    suite = TestSuite()
    p = cfg.byte_pause
    P = cfg.test_pause

    log.info("=" * 60)
    log.info("  SPI Bus LED-Observable Test Suite")
    log.info(f"  Bus: {cfg.bus}  Device: {cfg.device}")
    log.info(f"  Clock: {cfg.max_speed_hz / 1e3:.1f} kHz  Mode: {cfg.mode}")
    log.info(f"  Byte pause: {p * 1000:.0f} ms  Test pause: {P * 1000:.0f} ms")
    log.info("  Wire MISO → MOSI on the header for loopback tests")
    log.info("=" * 60)
    log.info("")

    spi = test_open_device(cfg, suite)
    if spi is None:
        log.error("Cannot open SPI device — aborting.")
        sys.exit(1)

    try:
        # ── Pin-coverage tests ───────────────────────────────────────────
        log.info("── Pin-coverage tests ──────────────────────────────────")
        log.info("  Each byte is a separate transaction:")
        log.info("  SCLK, MOSI, MISO, and CS are all individually visible.")
        log.info("")

        test_walking_ones_mosi(spi, suite, p)
        time.sleep(P)

        test_walking_zeros_mosi(spi, suite, p)
        time.sleep(P)

        test_cs_pulse(spi, suite, p, count=8)
        time.sleep(P)

        test_sclk_burst(spi, suite, p, count=8)
        time.sleep(P)

        test_alternating_bits(spi, suite, p)
        time.sleep(P)

        test_all_zeros(spi, suite, p)
        time.sleep(P)

        test_all_ones(spi, suite, p)
        time.sleep(P)

        test_multi_byte_loopback(spi, suite, p)
        time.sleep(P)

        # ── Full byte sweep ──────────────────────────────────────────────
        if not cfg.no_sweep:
            log.info("")
            log.info("── Full byte sweep ──────────────────────────────────────")
            test_full_byte_sweep(spi, suite, p)
            time.sleep(P)
        else:
            log.info("  (Full byte sweep skipped — pass without --no-sweep to enable)")

        # ── Configuration tests ──────────────────────────────────────────
        log.info("")
        log.info("── Configuration tests ─────────────────────────────────")

        test_spi_modes(spi, suite, p)
        spi.mode = cfg.mode           # restore original mode
        time.sleep(P)

        spi.max_speed_hz = cfg.max_speed_hz
        test_speed_modes(spi, suite, p)
        spi.max_speed_hz = cfg.max_speed_hz  # restore

    finally:
        spi.close()
        log.info("")

    success = suite.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
