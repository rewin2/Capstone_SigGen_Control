import spidev
import time

class LMX2820:
    def __init__(self, bus=0, cs=0, speed=10000000):
        """
        Initialize SPI interface and shadow register map.
        """
        self.spi = spidev.SpiDev()
        self.spi.open(bus, cs)
        self.spi.max_speed_hz = speed
        self.spi.mode = 0b00  # SPI Mode 0

        # Shadow register map (LMX2820 has 123 registers: R0–R122)
        self.regs = {i: 0x0000 for i in range(123)}


    def init_device(self, default_freq_ghz=1.0, fref=100):
            
        """
        Fully initialize the LMX2820 with default frequency = 1 GHz.
        This configures:
        - Reference and prescalers
        - PLL integer mode
        - Output chain (CHDIV mode for 1 GHz)
        - Calibrations
        """

        print("Initializing LMX2820...")

        # -------------------------------------------------------
        # 1. Reference and input path
        # -------------------------------------------------------
        self.write_reg(11, 0x0000)  # OSC_2X = 0 (no reference doubler)
        self.write_reg(12, 0x0400)  # MULT = 1 (reference multiplier bypass)
        self.write_reg(13, 0x0020)  # PLL_R = 1
        self.write_reg(14, 0x0001)  # PLL_R_PRE = 1

        # -------------------------------------------------------
        # 2. Set default frequency using the auto-banding function
        # -------------------------------------------------------
        print(f"Setting default output frequency to {default_freq_ghz} GHz")
        self.set_frequency(default_freq_ghz, fref)

        # -------------------------------------------------------
        # 3. Output power (default mid-level)
        # -------------------------------------------------------
        # R79 bits: OUTA_PWR (5:2)
        reg79 = self.set_bits(self.regs[79], 8, 5, 2)  
        self.write_reg(79, reg79)

        # -------------------------------------------------------
        # 4. Optional: lock detect setup (recommended)
        # -------------------------------------------------------
        self.write_reg(110, 0x00C0)  # Digital LD enabled

        # -------------------------------------------------------
        # 5. Final calibration pulse
        # -------------------------------------------------------
        self.write_reg(0, 0x0010)

        print("LMX2820 initialization complete.")

        # --------------------------------------------------------------
        # Low-level SPI write (correct for LMX2820)
        # --------------------------------------------------------------


    def set_frequency(self, freq_ghz, fref=100):
        """
        Set output frequency from 1–40 GHz with auto-band selection.
        fref is your reference frequency in MHz (default 100 MHz)
        """

        f_mhz = freq_ghz * 1000

        # -----------------------------------------------------
        # 1) Mode 1: 1–10 GHz  (Use CHDIV)
        # -----------------------------------------------------
        if 1 <= freq_ghz <= 10:
            out_mux = 0  # CHDIV
            # Aim to keep VCO between 6–12 GHz
            vco_target = 8000  
            chdiv = round(vco_target / f_mhz)
            internal_vco = f_mhz * chdiv
            print(f"Mode 1: CHDIV={chdiv}, VCO={internal_vco/1000:.3f} GHz")

        # -----------------------------------------------------
        # 2) Mode 2: 10–22 GHz (Use VCO direct)
        # -----------------------------------------------------
        elif 10 < freq_ghz <= 22:
            out_mux = 1  # VCO
            internal_vco = f_mhz * 0.5
            print(f"Mode 2: VCO direct at {internal_vco/1000:.3f} GHz")

        # -----------------------------------------------------
        # 3) Mode 3: 22–32 GHz (Mix of doubler vs direct)
        # -----------------------------------------------------
        elif 22 < freq_ghz <= 32:

            if freq_ghz < 30:
                out_mux = 2  # Doubler
                internal_vco = f_mhz * 0.25
                print(f"Mode 3A: VCO Doubler at {internal_vco/1000:.3f} GHz")
            else:
                out_mux = 1  # Direct
                internal_vco = f_mhz * 0.5
                print(f"Mode 3B: VCO direct at {internal_vco/1000:.3f} GHz")

        # -----------------------------------------------------
        # 4) Mode 4: 32–40 GHz (Use VCO Doubler exclusively)
        # -----------------------------------------------------
        elif 32 < freq_ghz <= 40:
            out_mux = 2  # Doubler
            internal_vco = f_mhz * 0.25
            print(f"Mode 4: VCO Doubler at {internal_vco/1000:.3f} GHz")

        else:
            raise ValueError("Frequency out of 1–40 GHz range")

        # -----------------------------------------------------
        # Compute PLL_N
        # -----------------------------------------------------
        pll_n = int(internal_vco / fref)
        num = 0
        den = 1

        # -----------------------------------------------------
        # Load registers
        # -----------------------------------------------------
        self.write_reg(36, pll_n)        # PLL_N
        self.write_reg(42, num)          # NUM
        self.write_reg(43, num)          # NUM
        self.write_reg(38, den >> 8)     # DEN MSB
        self.write_reg(39, den & 0xFF)   # DEN LSB

        # Output mux
        reg78 = self.set_bits(self.regs[78], out_mux, 1, 0)
        self.write_reg(78, reg78)

        # Trigger calibration
        self.write_reg(0, 0x0010)


    def write_reg(self, addr, value):
        """
        Write a 16-bit value to an LMX2820 register (24-bit frame).
        addr: register number (0–122)
        value: 16-bit register value
        """
        assert 0 <= addr <= 122, "Invalid register address"
        assert 0 <= value <= 0xFFFF, "Register value must be 16-bit"

        # First byte: (addr << 1) | 0  -> LSB=0 means WRITE
        addr_byte = (addr << 1) & 0xFE  
        
        msb = (value >> 8) & 0xFF
        lsb = value & 0xFF

        self.spi.xfer2([addr_byte, msb, lsb])

        # Save to local shadow copy
        self.regs[addr] = value

    # --------------------------------------------------------------
    # Optional: SPI read (LMX2820 supports readback)
    # --------------------------------------------------------------
    def read_reg(self, addr):
        """
        Read register via LMX2820 readback system.
        To read: write value with READBACK field set,
        then read from R0.
        """
        # Configure READBACK register (R0 bits 7:1)
        read_addr = (addr << 1)
        self.write_reg(0, read_addr)

        # Now clock out R0
        resp = self.spi.xfer2([0x01, 0x00, 0x00])
        return (resp[1] << 8) | resp[2]

    # --------------------------------------------------------------
    # Utility: bitfield setter
    # --------------------------------------------------------------
    def set_bits(self, regval, data, msb, lsb):
        """
        Insert `data` into bitfield msb:lsb of register value `regval`.
        """
        width = msb - lsb + 1
        mask = ((1 << width) - 1) << lsb
        return (regval & ~mask) | ((data << lsb) & mask)

    # --------------------------------------------------------------
    # HIGH-LEVEL CONFIG: Set individual fields directly
    # Example: set_field(78, "OUTA_MUX", 2)
    # --------------------------------------------------------------
    FIELDS = {
        # Register : (field_name, msb, lsb)
        (78, "OUTA_MUX"):      (1, 0),
        (78, "OUTA_PD"):       (6, 6),
        (79, "OUTA_PWR"):      (5, 2),
        (36, "PLL_N"):         (14, 0),
    }

    def set_field(self, reg, field, value):
        key = (reg, field)
        if key not in self.FIELDS:
            raise ValueError(f"Unknown field {field} in R{reg}")

        msb, lsb = self.FIELDS[key]
        regval = self.regs[reg]
        regval = self.set_bits(regval, value, msb, lsb)
        self.write_reg(reg, regval)

    # --------------------------------------------------------------
    # FULL INITIALIZATION FOR 40 GHz SIGNAL PATH
    # (LMX2820 = 10 GHz → Doubler = 20 GHz → External ×2 = 40 GHz)
    # --------------------------------------------------------------
