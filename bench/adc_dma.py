"""Logical GD32F30x ADC0 / DMA0 channel 0 subset; no hardware access.

Reference: GigaDevice GD32F30x User Manual Rev3.0, chapters 10 and 12.
Time is a configurable number of *executed instructions*, never ADC cycles.
Unsupported configurations stop explicitly instead of manufacturing progress.
"""
from collections import Counter
from emulate_clock_v121 import StopModel
from audit_ram_v121 import RAM, RAM_SIZE, hx

ADC_BASE = 0x40012400
ADC_DATA = ADC_BASE + 0x4C
DMA_BASE = 0x40020000
ADC_ON, CONT, CAL, RESET_CAL = 1, 2, 4, 8
ADC_DMA, LEFT, TRIGGER_ENABLE, SOFTWARE_START = 0x100, 0x800, 0x100000, 0x400000
SCAN = 0x100


class AdcDma:
    def __init__(self, read_memory, write_memory, profile=None, conversion_steps=64,
                 calibration_reads=2, log_limit=4096, adc_clock_enabled=lambda: True,
                 dma_clock_enabled=lambda: True):
        if conversion_steps < 1 or calibration_reads < 0:
            raise ValueError('ADC timing parameters must be nonnegative (conversion_steps >= 1)')
        self.read_memory, self.write_memory = read_memory, write_memory
        self.profile = profile
        self.conversion_steps = conversion_steps
        self.calibration_reads = calibration_reads
        self.log_limit = log_limit
        self.adc_clock_enabled = adc_clock_enabled
        self.dma_clock_enabled = dma_clock_enabled
        self.adc = {off: 0 for off in (0, 4, 8, 0xC, 0x10, 0x24, 0x28, 0x2C, 0x30, 0x34, 0x4C)}
        self.adc[0x24] = 0xFFF
        self.dma = {}
        for controller, channels in ((0, 7), (0x400, 5)):
            self.dma[controller] = self.dma[controller + 4] = 0
            for channel in range(channels):
                for offset in (0, 4, 8, 12):
                    self.dma[controller + 8 + channel * 20 + offset] = 0
        self.calibration_pending = {}
        self.calibration_events = []
        self.descriptors = []
        self.transfers = []
        self.total_transfers = 0
        self.completed_blocks = 0
        self.completed_sequences = 0
        self.channel_counts = Counter()
        self.conversion_counts = Counter()
        self.trigger_events = []
        self.active = False
        self.next_step = None
        self.rank = 0
        self.initial_count = 0
        self.dma_index = 0
        self.step = 0
        self.irq_requested = False

    def reset_adc(self):
        for off in self.adc:
            self.adc[off] = 0xFFF if off == 0x24 else 0
        self.calibration_pending.clear()
        self.active = False
        self.next_step = None
        self.rank = 0

    @staticmethod
    def access(offset, size, registers):
        if size != 4 or offset not in registers:
            raise StopModel('ADC/DMA register or access width not modelled')

    def sequence(self):
        length = ((self.adc[0x2C] >> 20) & 15) + 1
        return [(self.adc[0x34 if i < 6 else 0x30 if i < 12 else 0x2C] >> (5 * (i % 6))) & 31
                for i in range(length)]

    def sample(self, channel):
        if self.profile is None:
            raise StopModel('ADC conversion requires an explicit synthetic input profile')
        channels = self.profile['channels']
        if str(channel) not in channels:
            raise StopModel(f'ADC channel {channel} absent from synthetic profile')
        values = channels[str(channel)]
        if isinstance(values, int):
            values = [values]
        index = self.conversion_counts[channel]
        if index >= len(values):
            if not self.profile.get('repeat', False):
                raise StopModel(f'ADC channel {channel} synthetic samples exhausted')
            index %= len(values)
        return values[index]

    def read_adc(self, offset, size=4):
        self.access(offset, size, self.adc)
        if offset == 8 and self.adc_clock_enabled():
            for bit in list(self.calibration_pending):
                if self.calibration_pending[bit] == 0:
                    self.adc[8] &= ~bit
                    del self.calibration_pending[bit]
                    self.calibration_events.append(dict(step=self.step, bit=bit, state='completed'))
                else:
                    self.calibration_pending[bit] -= 1
        value = self.adc[offset]
        if offset == 0x4C:
            self.adc[0] &= ~2  # Reading ADC_RDATA clears EOC.
        return value

    def write_adc(self, offset, value, size=4):
        self.access(offset, size, self.adc)
        if not self.adc_clock_enabled():
            raise StopModel('ADC register write while ADC clock is gated/reset')
        if offset == 0x4C:
            raise StopModel('ADC_RDATA is read-only')
        if offset == 0:
            self.adc[0] &= value & 0x1F  # Status flags are cleared by writing zero.
            return
        if offset != 8:
            if self.active:
                raise StopModel('ADC reconfiguration during active conversion not modelled')
            masks = {4: 0x00CFFFFF, 0xC: 0xFFFFFF, 0x10: 0x3FFFFFFF,
                     0x24: 0xFFF, 0x28: 0xFFF, 0x2C: 0xFFFFFF,
                     0x30: 0x3FFFFFFF, 0x34: 0x3FFFFFFF}
            if value & ~masks[offset]:
                raise StopModel('ADC reserved register bits requested')
            self.adc[offset] = value
            return
        old = self.adc[8]
        if value & ~0xDE090F:
            raise StopModel('ADC_CTL1 unsupported/reserved bits')
        self.adc[8] = value
        if not value & ADC_ON:
            self.active = False
            self.next_step = None
            self.calibration_pending.clear()
            self.adc[8] &= ~(CAL | RESET_CAL | SOFTWARE_START)
            return
        for bit in (RESET_CAL, CAL):
            if value & bit and not old & bit:
                if self.active:
                    raise StopModel('ADC calibration while converting')
                self.calibration_pending[bit] = self.calibration_reads
                self.calibration_events.append(dict(step=self.step, bit=bit, state='started',
                                                   synthetic_poll_delay=self.calibration_reads))
        if value & SOFTWARE_START and not old & SOFTWARE_START:
            if ((value >> 17) & 7) == 7 and value & TRIGGER_ENABLE:
                self.start('SWRCST')
        elif old == value and old & ADC_ON and not value & (CAL | RESET_CAL):
            self.start('ADCON rewritten without other changes')

    def start(self, source):
        if self.calibration_pending:
            raise StopModel('ADC conversion requested before calibration completes')
        # The verified OEM path uses free-running regular scan. Other ADC modes
        # must be implemented and tested before being accepted.
        if self.adc[4] & ~SCAN:
            raise StopModel('ADC mode/interrupt/watchdog outside regular scan subset')
        channels = self.sequence()
        if not self.adc[4] & SCAN:
            channels = channels[:1]
        if any(channel > 17 for channel in channels):
            raise StopModel('ADC sequence includes reserved channel')
        if any(channel >= 16 for channel in channels) and not self.adc[8] & 0x800000:
            raise StopModel('ADC internal channels requested while TSVREN is disabled')
        # Validate all inputs before the first sample is allowed to affect RAM.
        for channel in channels:
            self.sample(channel)
        self.active = True
        self.rank = 0
        self.next_step = self.step + self.conversion_steps
        self.adc[8] &= ~SOFTWARE_START
        self.adc[0] |= 0x10
        self.trigger_events.append(dict(step=self.step, source=source, channels=channels,
                                       continuous=bool(self.adc[8] & CONT)))

    def read_dma(self, offset, size=4):
        self.access(offset, size, self.dma)
        return self.dma[offset] if offset not in (4, 0x404) else 0

    def write_dma(self, offset, value, size=4):
        self.access(offset, size, self.dma)
        if not self.dma_clock_enabled():
            raise StopModel('DMA register write while DMA clock is gated')
        controller = 0x400 if offset >= 0x400 else 0
        local = offset - controller
        if local == 0:
            raise StopModel('DMA_INTF is read-only')
        if local == 4:
            for ch in range(7 if controller == 0 else 5):
                flags = (value >> (4 * ch)) & 15
                clear = 15 if flags & 1 else flags
                self.dma[controller] &= ~(clear << (4 * ch))
                group = (self.dma[controller] >> (4 * ch)) & 14
                if not group:
                    self.dma[controller] &= ~(1 << (4 * ch))
            self.refresh_irq()
            return
        ch, field = divmod(local - 8, 20)
        base = controller + 8 + ch * 20
        old = self.dma[base]
        if field == 0:
            if value & ~0x7FFF:
                raise StopModel('DMA reserved channel control bits')
            if old & 1 and (old ^ value) & ~15:
                raise StopModel('DMA configuration changed while channel enabled')
            if value & 1 and not old & 1:
                if controller or ch:
                    raise StopModel('DMA engine only models ADC0 on DMA0 channel 0')
                self.validate_descriptor(value)
                self.initial_count = self.dma[12] & 0xFFFF
                self.dma_index = 0
                self.descriptors.append(self.descriptor(value))
            self.dma[offset] = value
        else:
            if old & 1:
                raise StopModel('DMA descriptor write while channel enabled')
            if field == 4 and value & ~0xFFFF:
                raise StopModel('DMA counter outside 16 bits')
            self.dma[offset] = value
        self.refresh_irq()

    def descriptor(self, control):
        return dict(step=self.step, control=hx(control), count=self.dma[12],
                    peripheral_address=hx(self.dma[16]), memory_address=hx(self.dma[20]),
                    peripheral_width=1 << ((control >> 8) & 3),
                    memory_width=1 << ((control >> 10) & 3),
                    memory_increment=bool(control & 0x80), circular=bool(control & 0x20))

    def validate_descriptor(self, control):
        if control & (0x4000 | 0x10 | 0x40) or self.dma[16] != ADC_DATA:
            raise StopModel('DMA source/direction outside ADC0 peripheral-to-memory subset')
        if ((control >> 8) & 3) != 1 or ((control >> 10) & 3) != 1:
            raise StopModel('ADC DMA supports only peripheral and memory halfwords')
        count = self.dma[12] & 0xFFFF
        memory = self.dma[20]
        span = count * 2 if control & 0x80 else (2 if count else 0)
        if memory & 1 or not RAM <= memory <= memory + span <= RAM + RAM_SIZE:
            raise StopModel('ADC DMA destination is unaligned or outside SRAM')

    def refresh_irq(self):
        flags, control = self.dma[0], self.dma[8]
        self.irq_requested = bool((flags & 2 and control & 2) or
                                  (flags & 4 and control & 4) or
                                  (flags & 8 and control & 8))

    def transfer(self, value, channel):
        control = self.dma[8]
        if not control & 1 or not self.dma[12]:
            return
        if not self.dma_clock_enabled():
            raise StopModel('ADC DMA request while DMA clock is gated')
        self.validate_descriptor(control)
        destination = self.dma[20] + (self.dma_index * 2 if control & 0x80 else 0)
        if not RAM <= destination <= RAM + RAM_SIZE - 2:
            raise StopModel('ADC DMA effective destination outside SRAM')
        encoded = value.to_bytes(2, 'little')
        self.write_memory(destination, encoded)
        if bytes(self.read_memory(destination, 2)) != encoded:
            raise StopModel('ADC DMA readback verification failed')
        self.dma[12] -= 1
        self.dma_index += 1
        self.total_transfers += 1
        self.channel_counts[channel] += 1
        if len(self.transfers) < self.log_limit:
            self.transfers.append(dict(step=self.step, channel=channel, rank=self.rank,
                value=value, destination=hx(destination), remaining=self.dma[12],
                verified=True, source='explicit synthetic profile'))
        if self.dma[12] == self.initial_count // 2:
            self.dma[0] |= 5
        if self.dma[12] == 0:
            self.dma[0] |= 3
            self.completed_blocks += 1
            if control & 0x20:
                self.dma[12] = self.initial_count
                self.dma_index = 0
        self.adc[0] &= ~2  # DMA consumes ADC_RDATA just like a peripheral read.
        self.refresh_irq()

    def advance(self, step):
        self.step = step
        if not self.active or step < self.next_step or not self.adc_clock_enabled():
            return
        channels = self.sequence() if self.adc[4] & SCAN else self.sequence()[:1]
        channel = channels[self.rank]
        sample = self.sample(channel)
        self.conversion_counts[channel] += 1
        value = sample << 4 if self.adc[8] & LEFT else sample
        self.adc[0x4C] = value
        end = self.rank + 1 == len(channels)
        if end:
            self.adc[0] |= 2
        if self.adc[8] & ADC_DMA:
            self.transfer(value, channel)
        self.rank += 1
        if end:
            self.completed_sequences += 1
            self.rank = 0
            if not self.adc[8] & CONT:
                self.active = False
                self.next_step = None
                return
        self.next_step = step + self.conversion_steps

    def describe(self):
        return dict(input_profile=self.profile, physical_inputs_measured=False,
            conversion_interval_executed_instructions=self.conversion_steps,
            calibration_delay_register_reads=self.calibration_reads, cycle_accurate=False,
            registers={hx(k): hx(v) for k, v in self.adc.items()},
            dma_registers={hx(k): hx(v) for k, v in self.dma.items() if v},
            configured_sequence=self.sequence(), triggers=self.trigger_events,
            calibration=self.calibration_events, descriptors=self.descriptors,
            total_transfers=self.total_transfers, completed_dma_blocks=self.completed_blocks,
            completed_sequences=self.completed_sequences, transfer_log=self.transfers,
            transfer_log_truncated=self.total_transfers > len(self.transfers),
            transfers_by_channel=dict(self.channel_counts), irq_requested=self.irq_requested)


def validate_profile(profile):
    if not isinstance(profile, dict) or profile.get('kind') != 'synthetic':
        raise ValueError('ADC profile must explicitly declare kind: synthetic')
    if not isinstance(profile.get('name'), str) or not profile['name'].strip():
        raise ValueError('ADC profile requires a name')
    channels = profile.get('channels')
    if not isinstance(channels, dict) or not channels:
        raise ValueError('ADC profile requires a nonempty channels object')
    if 'repeat' in profile and not isinstance(profile['repeat'], bool):
        raise ValueError('ADC repeat must be boolean')
    for key, values in channels.items():
        if not isinstance(key, str) or not key.isdecimal() or str(int(key)) != key or not 0 <= int(key) <= 17:
            raise ValueError('ADC channel keys must be canonical integers 0..17')
        values = [values] if type(values) is int else values
        if not isinstance(values, list) or not values:
            raise ValueError('ADC samples must be integers or nonempty lists')
        if any(type(v) is not int or not 0 <= v <= 4095 for v in values):
            raise ValueError('ADC samples must be 12-bit integers')
    return profile
