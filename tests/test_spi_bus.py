# test_spi_bus.py
#
# Standalone SPI bus functionality test
# Verifies the Pi's SPI peripheral is working correctly
# No LMX2820 knowledge — pure bus test

import spidev
import time

SPI_BUS      = 0
SPI_DEVICE   = 0
SPI_SPEED_HZ = 100_000   # 100 kHz

print("Opening SPI...")
spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)
spi.max_speed_hz  = SPI_SPEED_HZ
spi.mode          = 0b00
spi.bits_per_word = 8
spi.lsbfirst      = False
print(f"Opened /dev/spidev{SPI_BUS}.{SPI_DEVICE} at {SPI_SPEED_HZ//1000} kHz")

# Send a series of test bytes and print exactly what goes out
test_packets = [
    [0x00, 0x00, 0x00],   # all zeros
    [0xFF, 0xFF, 0xFF],   # all ones
    [0xAA, 0xAA, 0xAA],   # alternating 10101010
    [0x55, 0x55, 0x55],   # alternating 01010101
    [0x01, 0x57, 0xA0],   # R1 default value
    [0x00, 0x64, 0x71],   # R0 with FCAL_EN
]

print("\nSending test packets:")
print("-" * 40)

for packet in test_packets:
    response = spi.xfer2(packet)
    print(f"TX: {[hex(b) for b in packet]}  RX: {[hex(b) for b in response]}")
    time.sleep(0.1)

print("-" * 40)
spi.close()
print("Done")