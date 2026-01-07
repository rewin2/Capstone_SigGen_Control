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
    """

    def __init__(self):
        self.log = []

    def write(self, reg, value):
        value &= 0xFFFFFF  # LMX2820 is 24-bit
        entry = (reg, value)
        self.log.append(entry)

        print(f"[SPI MOCK] WRITE  R{reg:03d} = 0x{value:06X}")

    def clear_log(self):
        self.log.clear()

    def get_log(self):
        return list(self.log)

class RealSPI(SPIDriverBase):
    """
    Real SPI driver skeleton.
    Adapt this to your platform.
    """

    def __init__(self, spi_device):
        """
        spi_device: platform-specific SPI object
                    (e.g., spidev.SpiDev instance)
        """
        self.spi = spi_device

    def write(self, reg, value):
        value &= 0xFFFFFF

        # LMX2820 SPI format:
        # [15:8]  = register address
        # [23:0]  = data
        #
        # Typical format: 32-bit write
        word = ((reg & 0xFF) << 24) | value

        tx = [
            (word >> 24) & 0xFF,
            (word >> 16) & 0xFF,
            (word >> 8) & 0xFF,
            word & 0xFF,
        ]

        self.spi.xfer2(tx)
