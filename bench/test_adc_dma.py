"""Behavioral tests using independent expected DMA buffers and guard bytes."""
import struct
import unittest
from adc_dma import (AdcDma, ADC_DATA, ADC_ON, ADC_DMA, CONT, SCAN,
                     CAL, RESET_CAL, LEFT, SOFTWARE_START, TRIGGER_ENABLE,
                     validate_profile)
from audit_ram_v121 import RAM, RAM_SIZE
from emulate_clock_v121 import StopModel

CHANNELS = [6, 8, 9, 10, 11, 12, 15]
VALUES = [262, 520, 777, 1034, 1291, 1548, 1807]
DEST = RAM + 0xDA76
TRIGGER = ADC_ON | ADC_DMA | (7 << 17) | TRIGGER_ENABLE | SOFTWARE_START


class AdcDmaTest(unittest.TestCase):
    def setUp(self):
        self.memory = bytearray([0xA5] * RAM_SIZE)
        self.writes = []
        profile = validate_profile(dict(kind='synthetic', name='test', repeat=True,
                                       channels={str(c): v for c, v in zip(CHANNELS, VALUES)}))
        self.model = AdcDma(self.read, self.write, profile, conversion_steps=4)

    def read(self, address, count):
        return self.memory[address - RAM:address - RAM + count]

    def write(self, address, data):
        self.writes.append((address, data))
        self.memory[address - RAM:address - RAM + len(data)] = data

    def configure(self, circular=True, increment=True, count=7, destination=DEST):
        m = self.model
        m.write_dma(12, count)
        m.write_dma(16, ADC_DATA)
        m.write_dma(20, destination)
        m.write_dma(8, 0x2501 | (0x20 if circular else 0) | (0x80 if increment else 0))
        m.write_adc(4, SCAN)
        m.write_adc(0x2C, 6 << 20)
        m.write_adc(0x34, sum(c << (5 * i) for i, c in enumerate(CHANNELS[:6])))
        m.write_adc(0x30, 15)

    def run_samples(self, count):
        for _ in range(count):
            self.model.advance(self.model.step + 4)

    def test_dma_enable_alone_does_not_write_ram(self):
        self.configure()
        self.model.advance(1000)
        self.assertEqual(self.writes, [])
        self.assertEqual(self.model.dma[12], 7)

    def test_exact_seven_channel_order_halfwords_and_guards(self):
        self.configure()
        self.model.write_adc(8, TRIGGER)
        self.run_samples(7)
        self.assertEqual(self.read(DEST, 14), struct.pack('<7H', *VALUES))
        self.assertEqual([p for p, _ in self.writes], list(range(DEST, DEST + 14, 2)))
        self.assertEqual(self.read(DEST - 2, 2), b'\xA5\xA5')
        self.assertEqual(self.read(DEST + 14, 2), b'\xA5\xA5')
        self.assertEqual(self.model.completed_sequences, 1)
        self.assertEqual(self.model.completed_blocks, 1)
        self.assertEqual(self.model.dma[12], 7)
        self.assertEqual(self.model.dma[0] & 7, 7)
        self.assertFalse(self.model.irq_requested)

    def test_circular_dma_wraps_without_writing_after_buffer(self):
        self.configure()
        self.model.write_adc(8, TRIGGER | CONT)
        self.run_samples(21)
        self.assertEqual(len(self.writes), 21)
        self.assertEqual(self.model.completed_blocks, 3)
        self.assertEqual(self.model.completed_sequences, 3)
        self.assertEqual(self.writes[7][0], DEST)
        self.assertEqual(self.read(DEST + 14, 2), b'\xA5\xA5')

    def test_non_circular_counter_zero_stops_dma(self):
        self.configure(circular=False)
        self.model.write_adc(8, TRIGGER | CONT)
        self.run_samples(21)
        self.assertEqual(len(self.writes), 7)
        self.assertEqual(self.model.dma[12], 0)
        self.assertEqual(self.model.completed_sequences, 3)

    def test_fixed_destination(self):
        self.configure(increment=False)
        self.model.write_adc(8, TRIGGER)
        self.run_samples(7)
        self.assertEqual({p for p, _ in self.writes}, {DEST})
        self.assertEqual(self.read(DEST, 2), struct.pack('<H', VALUES[-1]))
        self.assertEqual(self.read(DEST + 2, 2), b'\xA5\xA5')

    def test_dma_disable_and_adc_disable_gate_transfers(self):
        self.configure()
        self.model.write_adc(8, TRIGGER | CONT)
        self.run_samples(1)
        self.model.write_dma(8, self.model.dma[8] & ~1)
        self.run_samples(7)
        self.assertEqual(len(self.writes), 1)
        self.model.write_adc(8, 0)
        conversions = dict(self.model.conversion_counts)
        self.run_samples(20)
        self.assertEqual(dict(self.model.conversion_counts), conversions)

    def test_dma_request_disable_does_not_copy_samples(self):
        self.configure()
        self.model.write_adc(8, TRIGGER & ~ADC_DMA)
        self.run_samples(7)
        self.assertEqual(self.writes, [])
        self.assertEqual(self.model.adc[0] & 2, 2)
        self.assertEqual(self.model.read_adc(0x4C), VALUES[-1])
        self.assertEqual(self.model.adc[0] & 2, 0)

    def test_calibration_exposes_busy_and_completes(self):
        m = self.model
        m.write_adc(8, ADC_ON)
        for bit in (RESET_CAL, CAL):
            m.write_adc(8, ADC_ON | bit)
            self.assertTrue(m.read_adc(8) & bit)
            self.assertTrue(m.read_adc(8) & bit)
            self.assertFalse(m.read_adc(8) & bit)
        self.assertEqual(len(m.calibration_events), 4)
        self.assertEqual(self.writes, [])

    def test_trigger_during_calibration_is_rejected(self):
        self.configure()
        self.model.write_adc(8, ADC_ON | CAL)
        with self.assertRaisesRegex(StopModel, 'before calibration'):
            self.model.write_adc(8, TRIGGER)
        self.assertEqual(self.writes, [])

    def test_adc_clock_source_trigger_gating(self):
        self.configure()
        self.model.write_adc(8, TRIGGER & ~TRIGGER_ENABLE)
        self.run_samples(10)
        self.assertEqual(self.writes, [])
        self.assertFalse(self.model.active)

    def test_left_alignment(self):
        self.configure()
        self.model.write_adc(8, TRIGGER | LEFT)
        self.run_samples(7)
        self.assertEqual(self.read(DEST, 14), struct.pack('<7H', *(v << 4 for v in VALUES)))

    def test_missing_input_rejects_before_any_dma_write(self):
        self.configure()
        self.model.profile['channels'].pop('15')
        with self.assertRaisesRegex(StopModel, 'channel 15 absent'):
            self.model.write_adc(8, TRIGGER)
        self.assertEqual(self.writes, [])

    def test_no_profile_is_an_explicit_stop(self):
        self.configure()
        self.model.profile = None
        with self.assertRaisesRegex(StopModel, 'explicit synthetic'):
            self.model.write_adc(8, TRIGGER)

    def test_finite_input_exhaustion(self):
        self.configure()
        self.model.profile['repeat'] = False
        self.model.write_adc(8, TRIGGER | CONT)
        self.run_samples(7)
        with self.assertRaisesRegex(StopModel, 'exhausted'):
            self.run_samples(1)
        self.assertEqual(len(self.writes), 7)

    def test_irq_flags_w1c_and_enables(self):
        self.configure()
        self.model.write_dma(8, self.model.dma[8] | 6)
        self.model.write_adc(8, TRIGGER)
        self.run_samples(7)
        self.assertTrue(self.model.irq_requested)
        self.model.write_dma(4, 2)
        self.assertEqual(self.model.dma[0] & 7, 5)
        self.assertTrue(self.model.irq_requested)
        self.model.write_dma(4, 1)
        self.assertEqual(self.model.dma[0] & 15, 0)
        self.assertFalse(self.model.irq_requested)

    def test_bad_destinations_never_modify_memory(self):
        for address in (RAM - 2, RAM + RAM_SIZE - 12, DEST + 1, 0x08006000):
            with self.subTest(address=hex(address)):
                with self.assertRaisesRegex(StopModel, 'destination'):
                    self.configure(destination=address)
                self.assertEqual(self.writes, [])

    def test_active_descriptor_mutation_rejected(self):
        self.configure()
        with self.assertRaisesRegex(StopModel, 'while channel enabled'):
            self.model.write_dma(20, DEST + 2)
        with self.assertRaisesRegex(StopModel, 'while channel enabled'):
            self.model.write_dma(8, self.model.dma[8] ^ 0x80)

    def test_wrong_direction_source_width_and_channel_rejected(self):
        for control, source, channel in ((0x25B1, ADC_DATA, 0), (0x25A1, ADC_DATA + 4, 0),
                                          (0x24A1, ADC_DATA, 0), (0x25A1, ADC_DATA, 1)):
            with self.subTest(control=hex(control), source=source, channel=channel):
                self.model.dma[16] = source
                self.model.dma[20] = DEST
                self.model.dma[12] = 7
                with self.assertRaises(StopModel):
                    self.model.write_dma(8 + 20 * channel, control)
                self.assertEqual(self.writes, [])

    def test_profile_validation(self):
        bad = [dict(kind='measured'), dict(kind='synthetic', name='x', channels={'6': -1}),
               dict(kind='synthetic', name='x', channels={'6': 4096}),
               dict(kind='synthetic', name='x', channels={'06': 0}),
               dict(kind='synthetic', name='x', channels={'6': True}),
               dict(kind='synthetic', name='x', channels={'6': []})]
        for profile in bad:
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                validate_profile(profile)

    def test_unknown_register_and_width_rejected(self):
        for method, args in ((self.model.read_adc, (0x14,)),
                             (self.model.read_adc, (8, 2)),
                             (self.model.write_dma, (0, 0)),
                             (self.model.read_dma, (0x100,))):
            with self.subTest(args=args), self.assertRaises(StopModel):
                method(*args)

    def test_adc_clock_gating_holds_conversion(self):
        self.configure()
        self.model.write_adc(8, TRIGGER)
        self.model.adc_clock_enabled = lambda: False
        self.run_samples(10)
        self.assertEqual(self.writes, [])
        self.model.adc_clock_enabled = lambda: True
        self.run_samples(1)
        self.assertEqual(len(self.writes), 1)

    def test_dma_clock_gating_stops_before_memory_write(self):
        self.configure()
        self.model.write_adc(8, TRIGGER)
        self.model.dma_clock_enabled = lambda: False
        with self.assertRaisesRegex(StopModel, 'DMA clock is gated'):
            self.run_samples(1)
        self.assertEqual(self.writes, [])

    def test_adc_reset_stops_and_clears_conversion_state(self):
        self.configure()
        self.model.write_adc(8, TRIGGER | CONT)
        self.run_samples(1)
        self.model.reset_adc()
        self.run_samples(10)
        self.assertEqual(len(self.writes), 1)
        self.assertEqual(self.model.adc[8], 0)
        self.assertEqual(self.model.adc[0x24], 0xFFF)


if __name__ == '__main__':
    unittest.main(verbosity=2)
