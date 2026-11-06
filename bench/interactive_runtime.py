"""Host-side interaction settings; reference scheduling stays available unchanged."""
import json
import queue
import threading
import time
from unicorn import UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from audit_ram_v121 import RAM, RAM_SIZE


def adc_can_batch(adc):
    return bool(adc.active and adc.adc_clock_enabled() and adc.dma_clock_enabled()
                and adc.profile and adc.profile.get('repeat')
                and all(type(value) is int for value in adc.profile['channels'].values())
                and adc.adc[8] & 0x100 and adc.dma.get(8, 0) & 1
                and not adc.dma.get(8, 0) & 14 and not adc.adc[4] & 0xE0)


def advance_adc_through(adc, step):
    """Retain every conversion at its exact old instruction deadline."""
    if adc.active and adc.next_step is not None and adc.next_step < adc.step:
        # A gated clock held the previous deadline. Resume at the current
        # instruction rather than inventing conversions while it was stopped.
        adc.next_step = step
    while adc.active and adc.next_step is not None and adc.next_step <= step:
        if not adc.adc_clock_enabled():
            break
        adc.advance(adc.next_step)
    adc.step = step


def peripheral_interval(runner):
    """Wake before the next enabled timer update, instead of polling all six."""
    delays = [4096]
    enabled=getattr(runner,"nvic_enable",[0xFFFFFFFF]*8)
    for timer, irq in runner.timers.values():
        if not enabled[irq//32]&(1<<(irq%32)) or not timer.clock_enabled() or not timer.regs[0xC] & 1:
            continue
        if timer.irq:
            delays.append(64)
        elif timer.regs[0] & 1:
            period = timer.prescaler + 1
            delays.append(max(1, (timer.regs[0x2C]+1-timer.regs[0x24])*period-timer.remainder))
    rtc=runner.backup
    if rtc.regs[0] & 7 and enabled[0]&(1<<3):
        if rtc.irq:delays.append(64)
        elif rtc.enabled() and not rtc.regs[4]&16:
            prescaler=(rtc.regs[8]<<16)|rtc.regs[12]
            period=(prescaler+1)*120_000_000
            delays.append(max(1,(period-rtc.fraction+32767)//32768))
    return min(delays)


class AdcWatch:
    """Synchronize DMA before CPU access to its destination, including writes."""
    def __init__(self, gate):
        self.gate = gate
        self.range = None
        self.handle = None
        adc = gate.r.adc_dma
        original = adc.write_dma
        def write(*args, **kwargs):
            result = original(*args, **kwargs)
            self.update()
            return result
        adc.write_dma = write
        self.update()

    def update(self):
        adc = self.gate.r.adc_dma
        count = adc.initial_count or adc.dma.get(12, 0)
        start = adc.dma.get(20, 0)
        end = start + (count*2 if adc.dma.get(8, 0) & 0x80 else 2)
        span = (start, end) if count and RAM <= start < end <= RAM+RAM_SIZE else None
        if span == self.range:
            return
        if self.handle is not None:
            self.gate.r.cpu.hook_del(self.handle)
            self.handle = None
        self.range = span
        if span:
            self.handle = self.gate.r.cpu.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE,
                lambda *args: self.gate.sync(), begin=start, end=end-1)


class ControlInbox:
    def __init__(self, stream):
        self.items = queue.Queue(maxsize=256)
        self.error = None
        self.thread = threading.Thread(target=self.read, args=(stream,), daemon=True)
        self.thread.start()

    def read(self, stream):
        try:
            for line in stream:
                if len(line) > 65536:
                    raise ValueError('Commande locale trop longue')
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError('Commande locale invalide')
                self.items.put(value)
        except (OSError, ValueError) as error:
            self.error = str(error)

    def drain(self):
        while True:
            try:
                yield self.items.get_nowait()
            except queue.Empty:
                return


def fast_lcd_gpio(runner, off, size, value):
    """Handle only LCD data/control pins; all other GPIO uses normal models.

    This changes host dispatch overhead. The ARM instructions and the GPIO
    write edges still execute; no drawing routine or firmware PC is replaced.
    """
    if size != 4 or not runner.lcd.armed:
        return False
    address = 0x40010000 + off
    if address == 0x4001180C:
        registers = runner.gpio[0x40011800]
        if (registers[12] ^ value) & ~0x7F80:
            return False
        registers[12] = value
        return True
    if address in (0x40010C10, 0x40010C14):
        mask = (value | (value >> 16)) & 65535 if address == 0x40010C10 else value
        if mask & ~0x2C00:
            return False
        registers = runner.gpio[0x40010C00]
        before = registers[12]
        after = ((before | (value & 65535)) & ~(value >> 16)) if address == 0x40010C10 else before & ~(value & 65535)
        registers[12] = after
        if not before & 0x400 and after & 0x400:
            runner.lcd.step = runner.steps
            runner.lcd.gpio(before, after, runner.gpio[0x40011800][12])
        return True
    return False
