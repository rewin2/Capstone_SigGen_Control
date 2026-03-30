"""
SPI Bus Functionality Test Suite
=================================
Tests an SPI bus using the spidev library (Linux/Raspberry Pi).
Run with: sudo python3 spi_test.py

Requirements:
    pip install spidev
    Enable SPI on Raspberry Pi via raspi-config or /boot/config.txt

Usage:
    sudo python3 spi_test.py [--bus 0] [--device 0] [--speed 1000000]
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
    bus: int = 0                  # SPI bus number (usually 0 or 1)
    device: int = 0               # Chip Select / device number
    max_speed_hz: int = 1_000_000 # Clock speed in Hz
    mode: int = 0                 # SPI mode 0–3
    bits_per_word: int = 8
    lsbfirst: bool = False


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
# Test helpers
# ──────────────────────────────────────────────────────────────────────────────

def timed_xfer(spi: spidev.SpiDev, data: List[int]) -> tuple[List[int], float]:
    """Transfer bytes and return (response, elapsed_ms)."""
    t0 = time.perf_counter()
    response = spi.xfer2(data)
    elapsed = (time.perf_counter() - t0) * 1000
    return response, elapsed


# ──────────────────────────────────────────────────────────────────────────────
# Individual tests
# ──────────────────────────────────────────────────────────────────────────────

def test_open_device(cfg: SPIConfig, suite: TestSuite) -> Optional[spidev.SpiDev]:
    """Open the SPI device and verify it is accessible."""
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
            details=f"/dev/spidev{cfg.bus}.{cfg.device} @ {cfg.max_speed_hz/1e6:.2f} MHz mode={cfg.mode}",
            duration_ms=elapsed,
        ))
        return spi
    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        suite.record(TestResult(
            name="Open device",
            passed=False,
            details=str(exc),
            duration_ms=elapsed,
        ))
        return None


def test_single_byte_loopback(spi: spidev.SpiDev, suite: TestSuite):
    """
    Send 0xA5 and expect it echoed back.
    Requires MISO connected to MOSI (hardware loopback).
    """
    payload = [0xA5]
    response, elapsed = timed_xfer(spi, payload)
    passed = response == payload
    suite.record(TestResult(
        name="Single-byte loopback (0xA5)",
        passed=passed,
        details=f"sent={payload} received={response}",
        duration_ms=elapsed,
    ))


def test_multi_byte_loopback(spi: spidev.SpiDev, suite: TestSuite):
    """Send a multi-byte pattern and verify the echo."""
    payload = [0x00, 0xFF, 0xAA, 0x55, 0x01, 0xFE, 0x7F, 0x80]
    response, elapsed = timed_xfer(spi, payload)
    passed = response == payload
    suite.record(TestResult(
        name="Multi-byte loopback",
        passed=passed,
        details=f"sent={[hex(b) for b in payload]} received={[hex(b) for b in response]}",
        duration_ms=elapsed,
    ))


def test_all_zeros(spi: spidev.SpiDev, suite: TestSuite):
    """Transfer all-zero bytes."""
    payload = [0x00] * 8
    response, elapsed = timed_xfer(spi, payload)
    passed = response == payload
    suite.record(TestResult(
        name="All-zeros transfer",
        passed=passed,
        details=f"received={response}",
        duration_ms=elapsed,
    ))


def test_all_ones(spi: spidev.SpiDev, suite: TestSuite):
    """Transfer all-0xFF bytes."""
    payload = [0xFF] * 8
    response, elapsed = timed_xfer(spi, payload)
    passed = response == payload
    suite.record(TestResult(
        name="All-ones transfer (0xFF)",
        passed=passed,
        details=f"received={response}",
        duration_ms=elapsed,
    ))


def test_alternating_bits(spi: spidev.SpiDev, suite: TestSuite):
    """Transfer alternating-bit patterns: 0xAA, 0x55."""
    for pattern, name in [(0xAA, "0xAA (10101010)"), (0x55, "0x55 (01010101)")]:
        payload = [pattern] * 4
        response, elapsed = timed_xfer(spi, payload)
        passed = response == payload
        suite.record(TestResult(
            name=f"Alternating bits {name}",
            passed=passed,
            details=f"received={[hex(b) for b in response]}",
            duration_ms=elapsed,
        ))


def test_walking_ones(spi: spidev.SpiDev, suite: TestSuite):
    """Walking-ones test: each byte shifts a single set bit left."""
    payload = [1 << i for i in range(8)]  # [0x01, 0x02, 0x04, … 0x80]
    response, elapsed = timed_xfer(spi, payload)
    passed = response == payload
    suite.record(TestResult(
        name="Walking-ones (0x01→0x80)",
        passed=passed,
        details=f"sent={[hex(b) for b in payload]} received={[hex(b) for b in response]}",
        duration_ms=elapsed,
    ))


def test_large_transfer(spi: spidev.SpiDev, suite: TestSuite, length: int = 256):
    """Transfer a large sequential block and verify integrity."""
    payload = [i % 256 for i in range(length)]
    response, elapsed = timed_xfer(spi, payload)
    passed = response == payload
    mismatches = [(i, payload[i], response[i]) for i in range(length) if payload[i] != response[i]]
    detail = f"{length} bytes, {len(mismatches)} mismatches" if not passed else f"{length} bytes OK"
    suite.record(TestResult(
        name=f"Large sequential transfer ({length} B)",
        passed=passed,
        details=detail,
        duration_ms=elapsed,
    ))


def test_speed_modes(spi: spidev.SpiDev, suite: TestSuite):
    """Verify the bus works at several common speeds."""
    speeds = [100_000, 500_000, 1_000_000, 4_000_000]
    payload = [0xA5, 0x5A]
    all_passed = True
    for speed in speeds:
        spi.max_speed_hz = speed
        response, elapsed = timed_xfer(spi, payload)
        if response != payload:
            all_passed = False
            log.warning(f"    Speed {speed//1000} kHz: FAIL (got {response})")
        else:
            log.info(f"    Speed {speed//1000} kHz: OK ({elapsed:.1f} ms)")
    suite.record(TestResult(
        name="Multi-speed loopback",
        passed=all_passed,
        details=f"tested {len(speeds)} speeds",
        duration_ms=0,
    ))


def test_spi_modes(spi: spidev.SpiDev, suite: TestSuite):
    """Test all four CPOL/CPHA combinations (modes 0–3)."""
    payload = [0xA5, 0x5A]
    all_passed = True
    for mode in range(4):
        spi.mode = mode
        try:
            response, elapsed = timed_xfer(spi, payload)
            ok = response == payload
            if not ok:
                all_passed = False
            log.info(f"    Mode {mode}: {'OK' if ok else 'FAIL'} (got {response})")
        except Exception as exc:
            all_passed = False
            log.warning(f"    Mode {mode}: exception — {exc}")
    suite.record(TestResult(
        name="All four SPI modes (0–3)",
        passed=all_passed,
        details="loopback at each CPOL/CPHA combination",
        duration_ms=0,
    ))


def test_throughput(spi: spidev.SpiDev, suite: TestSuite,
                    speed_hz: int = 1_000_000, block_size: int = 512, iterations: int = 20):
    """Measure sustained throughput over multiple transfers."""
    spi.max_speed_hz = speed_hz
    payload = [0xAA] * block_size
    total_bytes = 0
    t0 = time.perf_counter()
    for _ in range(iterations):
        spi.xfer2(payload)
        total_bytes += block_size
    elapsed_s = time.perf_counter() - t0
    kbps = (total_bytes * 8) / elapsed_s / 1000
    expected_kbps = speed_hz / 1000  # theoretical maximum
    passed = kbps >= expected_kbps * 0.1  # warn if <10 % of theoretical (software overhead is large)
    suite.record(TestResult(
        name="Throughput measurement",
        passed=passed,
        details=f"{kbps:.0f} kbps measured, {expected_kbps:.0f} kbps theoretical max",
        duration_ms=elapsed_s * 1000,
    ))


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def parse_args() -> SPIConfig:
    parser = argparse.ArgumentParser(description="SPI Bus Functionality Test")
    parser.add_argument("--bus",    type=int, default=0,         help="SPI bus number (default: 0)")
    parser.add_argument("--device", type=int, default=0,         help="Chip Select index (default: 0)")
    parser.add_argument("--speed",  type=int, default=1_000_000, help="Clock speed in Hz (default: 1 MHz)")
    parser.add_argument("--mode",   type=int, default=0,         help="SPI mode 0-3 (default: 0)")
    args = parser.parse_args()
    return SPIConfig(bus=args.bus, device=args.device,
                     max_speed_hz=args.speed, mode=args.mode)


def main():
    cfg = parse_args()
    suite = TestSuite()

    log.info("=" * 60)
    log.info("  SPI Bus Test Suite")
    log.info(f"  Bus: {cfg.bus}  Device: {cfg.device}  Speed: {cfg.max_speed_hz/1e6:.2f} MHz  Mode: {cfg.mode}")
    log.info("  NOTE: Loopback tests require MISO wired to MOSI")
    log.info("=" * 60)
    log.info("")

    spi = test_open_device(cfg, suite)
    if spi is None:
        log.error("Cannot open SPI device — aborting remaining tests.")
        sys.exit(1)

    try:
        log.info("── Loopback tests ──────────────────────────────────────")
        test_single_byte_loopback(spi, suite)
        test_multi_byte_loopback(spi, suite)
        test_all_zeros(spi, suite)
        test_all_ones(spi, suite)
        test_alternating_bits(spi, suite)
        test_walking_ones(spi, suite)
        test_large_transfer(spi, suite, length=256)

        log.info("")
        log.info("── Configuration tests ─────────────────────────────────")
        test_speed_modes(spi, suite)
        # Restore original mode after multi-mode test
        spi.mode = cfg.mode
        test_spi_modes(spi, suite)
        spi.mode = cfg.mode

        log.info("")
        log.info("── Performance tests ───────────────────────────────────")
        test_throughput(spi, suite, speed_hz=cfg.max_speed_hz)

    finally:
        spi.close()
        log.info("")

    success = suite.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
