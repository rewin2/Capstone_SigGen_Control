# lmx2820.py
#
# LMX2820 device driver (Integer-N)
#
# Aligned with:
#   - TI LMX2820 datasheet (SNAU251A) power-up sequence
#   - MIT Haystack Observatory LMX2820 driver
#

import time

from register_map import *
from write_order import STATIC_REGS, CAL_REGS, FREQ_REGS, OUTPUT_REGS


class PLLLockError(RuntimeError):
    pass


class LMX2820:
    def __init__(self, spi, gpio):
        self.spi = spi
        self.gpio = gpio
        self.reg_shadow = {}

    # -------------------------------------------------
    # Power control
    # -------------------------------------------------

    def power_on(self):
        self.gpio.power_enable(True)
        self.gpio.reset_pulse()

    def power_off(self):
        self.rf_enable(False)
        self.gpio.power_enable(False)

    def reset(self):
        self.power_off()

    # -------------------------------------------------
    # Initialization
    # -------------------------------------------------

    def initialize_registers(self):
        """
        Full power-up initialization sequence per datasheet section 8.3
        and MIT Haystack Observatory driver.

        Sequence:
            1. Software RESET = 1
            2. Software RESET = 0
            3. Write ALL registers R122 → R1, R0 last with FCAL_EN=0
            4. Wait 10ms for internal LDOs to stabilize
            5. Write R0 with FCAL_EN=1 to trigger VCO calibration
        """
        from utils import load_register_file

        # Load all 123 registers from TI default file
        reg_image = load_register_file(
            "data/HexRegisterValuesInitialState.txt"
        )

        # Step 1: Assert RESET = 1
        self.write_register(
            SYS_CTRL_REG,
            reg_image[SYS_CTRL_REG] | RESET_MASK
        )

        # Step 2: Deassert RESET = 0, FCAL_EN = 0
        self.write_register(
            SYS_CTRL_REG,
            reg_image[SYS_CTRL_REG] & ~RESET_MASK & ~FCAL_EN_MASK
        )

        # Step 3: Write all registers R122 → R0
        # R0 written last with FCAL_EN=0 — calibration not valid yet
        for reg in range(122, -1, -1):
            value = reg_image[reg]
            if reg == SYS_CTRL_REG:
                value = value & ~FCAL_EN_MASK   # ensure no premature cal
            self.write_register(reg, value)

        # Step 4: Wait for LDOs to stabilize
        time.sleep(0.010)

        # Step 5: Trigger VCO calibration with stable LDOs
        r0_cal = reg_image[SYS_CTRL_REG] | FCAL_EN_MASK
        self.write_register(SYS_CTRL_REG, r0_cal)

        self.rf_enable(False)

    # -------------------------------------------------
    # RF Enable
    # -------------------------------------------------

    def rf_enable(self, enable: bool):
        """
        Enable or disable RF output A via OUTA_PD register bit.

        NOTE: OUTA_PD is active-HIGH power-down:
            enable=True  → OUTA_PD=0 (output active)
            enable=False → OUTA_PD=1 (output powered down)
        """
        self.write_field(
            RFOUTA_EN_REG,
            RFOUTA_EN_MASK,
            RFOUTA_EN_SHIFT,
            0 if enable else 1,
        )

    # -------------------------------------------------
    # Low-level register writes
    # -------------------------------------------------

    def write_register(self, reg: int, value: int):
        if not (0 <= value <= 0xFFFF):
            raise ValueError(
                f"Register value out of range: 0x{value:X}"
            )
        self.reg_shadow[reg] = value
        self.spi.write(reg, value)

    def write_field(self, reg: int, mask: int, shift: int, value: int):
        if value < 0:
            raise ValueError("Field value cannot be negative")
        current = self.reg_shadow.get(reg, 0)
        new_value = (current & ~mask) | ((value << shift) & mask)
        self.write_register(reg, new_value)

    # -------------------------------------------------
    # CHDIV encoding
    # -------------------------------------------------

    def encode_chdiv(self, chdiv: int) -> int:
        """
        Encode CHDIV divide ratio to LMX2820 register field value.

        Divide ratio → encoded value:
            2   → 0
            4   → 1
            8   → 2
            16  → 3
            32  → 4
            64  → 5
            128 → 6
        """
        encoding = {
            2:   0,
            4:   1,
            8:   2,
            16:  3,
            32:  4,
            64:  5,
            128: 6,
        }
        if chdiv not in encoding:
            raise ValueError(f"Invalid CHDIV value: {chdiv}")
        return encoding[chdiv]

    # -------------------------------------------------
    # GPIO Output Routing
    # -------------------------------------------------

    def configure_output_path(self, plan: dict):
        """
        Configure SP4T switch and external doubler via GPIO
        based on frequency band.

        Band → SP4T position:
            "1_10"  → 0  (divider or direct VCO, no doubler)
            "10_22" → 1  (direct VCO or internal doubler)
            "22_30" → 2  (internal + external doubler)
            "30_40" → 3  (internal + external doubler)
        """
        band             = plan["band"]
        external_doubler = plan.get("external_doubler", False)

        if band == "1_10":
            self.gpio.set_sp4t(0)
            self.gpio.external_doubler_enable(False)

        elif band == "10_22":
            self.gpio.set_sp4t(1)
            self.gpio.external_doubler_enable(False)

        elif band == "22_30":
            self.gpio.set_sp4t(2)
            self.gpio.external_doubler_enable(True)

        elif band == "30_40":
            self.gpio.set_sp4t(3)
            self.gpio.external_doubler_enable(True)

        else:
            raise ValueError(f"Unknown band: '{band}'")

        # Consistency check — external_doubler flag must match band
        if external_doubler != (band in ("22_30", "30_40")):
            raise ValueError(
                f"external_doubler flag inconsistent with band '{band}'"
            )

    # -------------------------------------------------
    # PLL Programming (Integer-N)
    # -------------------------------------------------

    def program_pll(self, N: int, instacal_2x: int = 0, instcal_pll: int = 0):
        """
        Program integer-N PLL divider and associated calibration registers.

        Args:
            N           : integer PLL divider value (12–32767)
            instacal_2x : 1 if internal doubler engaged, else 0
                          Controls R1 bit 1 per MIT driver
            instcal_pll : instant calibration value
                          Always 0 for integer-N (NUM=0)
                          Would be int(2^32 * NUM/DEN) for fractional

        Register writes:
            R36 : PLL_N
            R35 : MASH_ORDER = 0 (integer mode)
            R44 : INSTCAL_PLL MSB
            R45 : INSTCAL_PLL LSB
            R1  : InstaCal_2x bit
        """

        # Integer N value
        self.write_field(
            PLL_N_REG,
            PLL_N_MASK,
            PLL_N_SHIFT,
            N & 0x7FFF,
        )

        # MASH order = integer (0)
        self.write_field(
            MASH_CTRL_REG,
            MASH_ORDER_MASK,
            MASH_ORDER_SHIFT,
            MASH_INTEGER,
        )

        # INSTCAL_PLL MSB and LSB (always 0 for integer-N)
        instcal_msb = (instcal_pll >> 16) & 0xFFFF
        instcal_lsb = instcal_pll & 0xFFFF

        self.write_field(
            INSTCAL_MSB_REG,
            INSTCAL_MSB_MASK,
            INSTCAL_MSB_SHIFT,
            instcal_msb,
        )

        self.write_field(
            INSTCAL_LSB_REG,
            INSTCAL_LSB_MASK,
            INSTCAL_LSB_SHIFT,
            instcal_lsb,
        )

        # InstaCal_2x — set when doubler path is active
        self.write_field(
            INSTACAL_2X_REG,
            INSTACAL_2X_MASK,
            INSTACAL_2X_SHIFT,
            instacal_2x,
        )

    # -------------------------------------------------
    # Frequency Programming (Single Authority)
    # -------------------------------------------------

    def apply_frequency_plan(self, plan: dict):
        """
        Apply a complete frequency plan to the device.

        Sequence:
            0. RF OFF
            1. GPIO routing (SP4T + external doubler)
            2. Program PLL N, INSTCAL, InstaCal_2x
            3. CHDIV (divider path only)
            4. OUTA_MUX
            5. Wait 10ms for register values to settle
            6. Trigger VCO calibration (write R0 with FCAL_EN=1)
            7. Poll lock detect
            8. RF ON
        """

        # 0. RF OFF
        self.rf_enable(False)

        # 1. GPIO routing — switch before any register writes
        self.configure_output_path(plan)

        # 2. Program PLL
        self.program_pll(
            N=plan["N"],
            instacal_2x=plan.get("instacal_2x", 0),
            instcal_pll=plan.get("instcal_pll", 0),
        )

        # 3. CHDIV — only needed on divider path
        if plan["outa_mux"] == 0:
            if plan["chdiv"] is None:
                raise ValueError("CHDIV required when OUTA_MUX = 0")
            chdiv_code = self.encode_chdiv(plan["chdiv"])
            self.write_field(
                CHDIV_REG,
                CHDIV_MASK,
                CHDIV_SHIFT,
                chdiv_code,
            )

        # 4. OUTA_MUX
        self.write_field(
            OUTA_MUX_REG,
            OUTA_MUX_MASK,
            OUTA_MUX_SHIFT,
            plan["outa_mux"],
        )

        # 5. Wait for register values to settle before calibration
        # Per MIT driver and datasheet recommendation
        time.sleep(0.010)

        # 6. Trigger VCO calibration — write R0 with FCAL_EN=1
        for reg in CAL_REGS:
            cal_value = self.reg_shadow.get(reg, 0) | FCAL_EN_MASK
            self.spi.write(reg, cal_value)

        # 7. Poll lock detect with glitch filtering
        LOCK_CONFIRM_COUNT   = 3
        LOCK_TIMEOUT_S       = 0.1
        LOCK_POLL_INTERVAL_S = 0.001

        lock_start    = time.time()
        elapsed       = 0.0
        confirm_count = 0

        while confirm_count < LOCK_CONFIRM_COUNT:
            if self.gpio.read_lock_detect():
                confirm_count += 1
            else:
                confirm_count = 0   # reset on any glitch

            if elapsed >= LOCK_TIMEOUT_S:
                raise PLLLockError(
                    "PLL failed to lock within timeout"
                )

            time.sleep(LOCK_POLL_INTERVAL_S)
            elapsed += LOCK_POLL_INTERVAL_S

        lock_time_ms = (time.time() - lock_start) * 1000
        print(f"[DEBUG] PLL locked in {lock_time_ms:.2f} ms")

        # 8. RF ON
        self.rf_enable(True)