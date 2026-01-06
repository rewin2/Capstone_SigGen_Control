frequency_plan.py

from dataclasses import dataclass

@dataclass
class FrequencyPlan:
    freq_ghz: float
    mode: int
    pll_n: int
    pll_num: int
    pll_den: int
    chdiv: int
    outa_mux: int

def compute_frequency_plan(freq_ghz, fref_mhz=100):
    """
    Integer-N frequency planner for LMX2820.
    Enforces 100 MHz step size.
    """

    if not (1.0 <= freq_ghz <= 40.0):
        raise ValueError("Frequency out of range (1–40 GHz)")

    freq_mhz = freq_ghz * 1000.0

    # Enforce 100 MHz step size
    if freq_mhz % fref_mhz != 0:
        raise ValueError(
            "Integer-N mode requires frequency steps of 100 MHz"
        )

    # --------------------------------------------------
    # Output mode selection
    # --------------------------------------------------

    # Mode 1: 1–10 GHz → CHDIV
    if freq_ghz <= 10.0:
        mode = 1
        outa_mux = 0      # CHDIV
        ext_mult = 2
        int_mult = 1

        # Choose CHDIV so VCO stays ~8 GHz
        vco_target_mhz = 8000
        chdiv = int(round((vco_target_mhz * ext_mult) / freq_mhz))
        vco_mhz = freq_mhz * chdiv / ext_mult

    # Mode 2: 10–22 GHz → VCO direct
    elif freq_ghz <= 22.0:
        mode = 2
        outa_mux = 1      # VCO
        ext_mult = 2
        int_mult = 1
        chdiv = 1

        vco_mhz = freq_mhz / ext_mult

    # Mode 3: 22–32 GHz → internal doubler
    elif freq_ghz <= 32.0:
        mode = 3
        outa_mux = 2      # DOUBLER
        ext_mult = 2
        int_mult = 2
        chdiv = 1

        vco_mhz = freq_mhz / (ext_mult * int_mult)

    # Mode 4: 32–40 GHz → internal doubler
    else:
        mode = 4
        outa_mux = 2      # DOUBLER
        ext_mult = 2
        int_mult = 2
        chdiv = 1

        vco_mhz = freq_mhz / (ext_mult * int_mult)

    # --------------------------------------------------
    # Integer-N PLL calculation
    # --------------------------------------------------

    pll_n = int(vco_mhz / fref_mhz)

    # Verify exact integer-N
    if pll_n * fref_mhz != vco_mhz:
        raise ValueError(
            "Frequency cannot be generated exactly in integer-N mode"
        )

    pll_num = 0
    pll_den = 1

    return FrequencyPlan(
        freq_ghz=freq_ghz,
        mode=mode,
        pll_n=pll_n,
        pll_num=pll_num,
        pll_den=pll_den,
        chdiv=chdiv,
        outa_mux=outa_mux
    )

def apply_field_to_image(self, field, value):
    info = REGISTER_MAP[field]

    # Multi-register (16-bit) fields
    if isinstance(info["reg"], tuple):
        msb_reg, lsb_reg = info["reg"]
        self.reg_image[msb_reg] = (value >> 8) & 0xFF
        self.reg_image[lsb_reg] = value & 0xFF
        return [msb_reg, lsb_reg]

    # Bitfield inside a single register
    reg = info["reg"]
    msb = info["msb"]
    lsb = info["lsb"]

    mask = ((1 << (msb - lsb + 1)) - 1) << lsb
    self.reg_image[reg] &= ~mask
    self.reg_image[reg] |= (value << lsb) & mask

    return [reg]

def apply_frequency_plan(self, plan):
    touched_registers = set()

    for field, value in plan.items():
        regs = self.apply_field_to_image(field, value)
        touched_registers.update(regs)

    # Write only modified registers to hardware
    for reg in sorted(touched_registers):
        self.write_reg(reg, self.reg_image[reg])

    # Trigger calibration (FCAL)
    self.write_reg(0, self.reg_image[0] | 0x0010)