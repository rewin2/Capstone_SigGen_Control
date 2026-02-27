# spi.py
#
# SPI driver abstraction for LMX2820
#
# Responsibilities:
# - Provide a write(reg, value) interface
# - Hide platform-specific SPI details
#
# Does NOT:
# - Know about registers meaning
# - Know about PLL math
# - Know about FSM or device logic


class SPIDriverBase:
    """
    Abstract SPI driver interface.
    """

    def write(self, reg, value):
        """
        Write a value to a register.

        Args:
            reg   (int): Register address
            value (int): Register value (up to 24 bits)
        """
        raise NotImplementedError

class MockSPI(SPIDriverBase):
    """
    Mock SPI driver for simulation and testing.
    Behaviorally identical to RealSPI - same validation, same format.
    """

    def __init__(self):
        self.log = []

    def write(self, reg: int, value: int):
        """
        Simulate a 24-bit LMX2820 SPI write.

        Packet format mirrors RealSPI:
            Byte 0: 7-bit register address (MSB=0 for write)
            Byte 1: Data high byte (bits 15:8)
            Byte 2: Data low byte  (bits 7:0)
        """
        if not (0 <= reg <= 0x7F):
            raise ValueError(f"Register address out of range: {reg}")

        if not (0 <= value <= 0xFFFF):
            raise ValueError(f"Register value out of range: 0x{value:X}")

        entry = (reg, value)
        self.log.append(entry)

        if isinstance(reg, int):
            reg_str = f"R{reg:03d}"
        else:
            reg_str = reg

        print(f"[SPI MOCK] WRITE  {reg_str} = 0x{value:04X}")

    def close(self):
        """
        No-op for mock driver. Mirrors RealSPI interface.
        """
        pass

    def clear_log(self):
        self.log.clear()

    def get_log(self):
        return list(self.log)

class RealSPI(SPIDriverBase):
    """
    Real SPI driver for LMX2820 on Raspberry Pi using spidev.

    LMX2820 SPI format (from datasheet section 6.6):
        - 24-bit words (3 bytes), MSB first
        - Mode 0 (CPOL=0, CPHA=0)
        - Max SCK frequency: 40 MHz
        - Packet format: [A6:A0] [D15:D8] [D7:D0]
            Byte 0: 7-bit register address (bits 22:16)
            Byte 1: Data high byte         (bits 15:8)
            Byte 2: Data low byte          (bits 7:0)
    """

    def __init__(self, bus: int = 0, device: int = 0, speed_hz: int = 10_000_000):
        """
        Args:
            bus      : SPI bus number (default 0)
            device   : CE pin / chip select (default 0)
            speed_hz : Clock speed in Hz (default 10 MHz, datasheet max is 40 MHz)
        """
        import spidev

        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)

        self.spi.max_speed_hz = speed_hz
        self.spi.mode         = 0b00   # Mode 0: CPOL=0, CPHA=0
        self.spi.bits_per_word = 8
        self.spi.lsbfirst     = False  # MSB first

    def write(self, reg: int, value: int):
        """
        Write a 16-bit value to a 7-bit LMX2820 register address.

        Packet is 24 bits, sent MSB first:
            Byte 0: [0, A6, A5, A4, A3, A2, A1, A0]  ← address, MSB=0 for write
            Byte 1: [D15, D14, D13, D12, D11, D10, D9, D8]
            Byte 2: [D7,  D6,  D5,  D4,  D3,  D2,  D1, D0]
        """
        if not (0 <= reg <= 0x7F):
            raise ValueError(f"Register address out of range: {reg}")

        if not (0 <= value <= 0xFFFF):
            raise ValueError(f"Register value out of range: 0x{value:X}")

        tx = [
            reg & 0x7F,           # address byte, bit7=0 indicates write
            (value >> 8) & 0xFF,  # data high byte
            value & 0xFF,         # data low byte
        ]

        self.spi.xfer2(tx)

    def close(self):
        """
        Release the SPI device. Call during system shutdown.
        """
        self.spi.close()
