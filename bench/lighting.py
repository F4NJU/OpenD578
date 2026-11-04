"""Observe the OEM 12-bit lighting bus: PA5 latch, PB3 clock, PB4 data.

LCD intensity is channel 8 (OEM sleep/wake and brightness-menu callers).
Other channels are retained without assigning unmeasured physical LED colors.
"""
from collections import deque
from emulate_clock_v121 import StopModel


class LightingBus:
    def __init__(self):
        self.armed=False
        self.active=False
        self.bits=[]
        self.expected=deque()
        self.registers={}
        self.frames=[]
        self.crosschecks=0

    def gpio(self,before_a,after_a,before_b,after_b,step):
        if not self.armed:return
        if before_a & 0x20 and not after_a & 0x20:
            self.active=True
            self.bits=[]
        if self.active and not before_b & 8 and after_b & 8:
            self.bits.append(1 if after_b & 16 else 0)
        if not before_a & 0x20 and after_a & 0x20 and self.active:
            self.active=False
            if len(self.bits)!=12:
                raise StopModel('lighting frame does not contain 12 GPIO clock edges')
            value=0
            for bit in self.bits:value=value*2+bit
            address,data=value>>8,value&255
            if self.expected:
                expected=self.expected.popleft()
                if expected != (address,data):
                    raise StopModel('lighting GPIO frame disagrees with OEM call arguments')
                self.crosschecks+=1
            self.registers[address]=data
            self.frames.append(dict(step=step,address=address,value=data))

    def describe(self):
        return dict(registers={str(k):v for k,v in self.registers.items()},
                    lcd_brightness=self.registers.get(8),frames=self.frames,
                    gpio_crosschecks=self.crosschecks,
                    wiring=dict(latch='PA5',clock='PB3',data='PB4'),
                    physical_key_led_colors_qualified=False)
