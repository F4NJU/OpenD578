"""Read-only GD32F303 HD/XD clock decode with the user-confirmed 12 MHz HXTAL.

Reference: GigaDevice GD32F30x User Manual, RCU_CFG0/CFG1, HD/XD clock tree.
This describes register-derived frequencies, not a cycle-accurate CPU emulator.
"""
HXTAL_HZ = 12_000_000


def describe_clock(regs, systick=None, hxtal_hz=HXTAL_HZ):
    cfg = regs[4]
    source = (cfg >> 2) & 3
    code = ((cfg >> 18) & 15) | (((cfg >> 27) & 1) << 4) | (((cfg >> 30) & 1) << 5)
    factor = min(63, code + (2 if code < 15 else 1))
    pll_input = (48_000_000 if regs.get(0x2C, 0) & (1 << 30) else hxtal_hz) if cfg & (1 << 16) else 4_000_000
    if cfg & (1 << 16) and cfg & (1 << 17):
        pll_input //= 2
    sys_hz = (8_000_000, hxtal_hz, pll_input * factor, None)[source]
    ahb_div = (1,1,1,1,1,1,1,1,2,4,8,16,64,128,256,512)[(cfg >> 4) & 15]
    apb_div = (1,1,1,1,2,4,8,16)
    hclk = sys_hz // ahb_div if sys_hz else None
    pclk1 = hclk // apb_div[(cfg >> 8) & 7] if hclk else None
    pclk2 = hclk // apb_div[(cfg >> 11) & 7] if hclk else None
    tick_hz = hclk if systick and systick[0x10] & 4 else hclk // 8 if hclk else None
    period = (systick[0x14]+1)/tick_hz if systick and tick_hz else None
    return dict(HXTAL_Hz=hxtal_hz,HXTAL_source='user-confirmed crystal marking 12.00 MHz',
        RCU_CFG0=hex(cfg),RCU_CFG1=hex(regs.get(0x2C,0)),system_source=('IRC8M','HXTAL','PLL','unknown')[source],
        PLL_input_Hz=pll_input,PLL_multiplier=factor,SYS_Hz=sys_hz,HCLK_Hz=hclk,
        PCLK1_Hz=pclk1,PCLK2_Hz=pclk2,SysTick_Hz=tick_hz,SysTick_period_seconds=period,
        scope='HD/XD register decode; instruction timing remains synthetic',cycle_accurate=False)


def calibration_observation(cpu, qualified):
    if not qualified:
        return dict(qualified=False,power_drive_bytes=None,supply_byte=None,
                    frequency_trim=None,RX_gain=None,deviation=None)
    return dict(qualified=True,power_drive_base='0x20009410',
        power_drive_bytes=list(cpu.mem_read(0x20009411,4)),
        supply_byte=bytes(cpu.mem_read(0x20009404,1))[0],
        frequency_trim=None,RX_gain=None,deviation=None,
        evidence='V1.21 RAM reads; selector 0x08065194; raw control values, not watts')
