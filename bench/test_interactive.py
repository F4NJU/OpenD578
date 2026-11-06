import io
import struct
import unittest
from types import SimpleNamespace
import test_adc_dma as fixture_module
from test_adc_dma import TRIGGER, CONT, DEST, VALUES
from interactive_runtime import (adc_can_batch, advance_adc_through, peripheral_interval,
                                 ControlInbox, fast_lcd_gpio)
from board_clock import describe_clock, calibration_observation
from timers import Timer
from lcd_bus import LcdBus


class InteractiveTests(unittest.TestCase):
    def model(self):
        fixture=fixture_module.AdcDmaTest();fixture.setUp();fixture.configure()
        fixture.model.write_adc(8,TRIGGER|CONT)
        return fixture

    def test_batched_conversions_match_each_individual_deadline_and_guard_bytes(self):
        reference=self.model();batched=self.model()
        for step in range(1,4001):reference.model.advance(step)
        advance_adc_through(batched.model,4000)
        self.assertEqual(batched.memory,reference.memory)
        self.assertEqual(batched.writes,reference.writes)
        self.assertEqual(batched.model.transfers,reference.model.transfers)
        self.assertEqual(batched.model.completed_sequences,reference.model.completed_sequences)
        self.assertEqual(batched.model.next_step,reference.model.next_step)
        self.assertEqual(len(batched.writes),1000)

    def test_interrupt_enabled_dma_uses_reference_deadlines(self):
        f=self.model();self.assertTrue(adc_can_batch(f.model))
        f.model.write_dma(8,f.model.dma[8]|2)
        self.assertFalse(adc_can_batch(f.model))

    def test_finite_or_varying_samples_use_reference_deadlines(self):
        f=self.model();f.model.profile['repeat']=False
        self.assertFalse(adc_can_batch(f.model))
        f.model.profile['repeat']=True;f.model.profile['channels']['6']=[1,2]
        self.assertFalse(adc_can_batch(f.model))

    def test_clock_gating_does_not_create_missed_conversions_on_resume(self):
        f=self.model();f.model.adc_clock_enabled=lambda:False
        advance_adc_through(f.model,1000)
        self.assertEqual(f.writes,[])
        f.model.adc_clock_enabled=lambda:True
        advance_adc_through(f.model,1001)
        self.assertEqual(len(f.writes),1)
        self.assertEqual(f.model.next_step,1005)

    def test_timer_wakes_before_first_enabled_irq_without_polling_disabled_timers(self):
        timer=Timer('test');timer.prescaler=999
        timer.regs.update({0:1,12:1,0x2C:119,0x24:119});timer.remainder=750
        r=SimpleNamespace(timers={1:(timer,55)},backup=SimpleNamespace(regs={0:0}))
        self.assertEqual(peripheral_interval(r),250)
        timer.regs[0]=0
        self.assertEqual(peripheral_interval(r),4096)

    def test_RTC_second_interrupt_is_scheduled_at_its_actual_deadline(self):
        from backup_rtc import BackupRtc
        rtc=BackupRtc();rtc.regs[0]=1;rtc.regs[4]=0x28;rtc.regs[12]=32767
        rtc.fraction=32768*120_000_000-16*32768
        runner=SimpleNamespace(timers={},backup=rtc,nvic_enable=[8]*8)
        self.assertEqual(peripheral_interval(runner),16)
        runner.nvic_enable=[0]*8
        self.assertEqual(peripheral_interval(runner),4096)

    def test_pipe_retains_command_order_and_stop(self):
        inbox=ControlInbox(io.StringIO('{"control":"KEY_SET","keys":["MENU"]}\n{"control":"STOP"}\n'))
        inbox.thread.join(timeout=1)
        self.assertIsNone(inbox.error)
        self.assertEqual([c['control'] for c in inbox.drain()],['KEY_SET','STOP'])

    def test_clock_decode_uses_12MHz_crystal_and_programmed_PLL(self):
        c=describe_clock({4:0x21840A,0x2C:0},{0x10:3,0x14:75000})
        self.assertEqual(c['HCLK_Hz'],120_000_000)
        self.assertEqual(c['PCLK1_Hz'],60_000_000)
        self.assertEqual(c['PCLK2_Hz'],120_000_000)
        self.assertAlmostEqual(c['SysTick_period_seconds'],75001/15_000_000)
        self.assertEqual(describe_clock({4:4})['HCLK_Hz'],12_000_000)
        self.assertEqual(describe_clock({4:0})['HCLK_Hz'],8_000_000)

    def test_unknown_calibration_does_not_report_values(self):
        cpu=SimpleNamespace(mem_read=lambda *args:(_ for _ in ()).throw(AssertionError('unexpected RAM read')))
        self.assertIsNone(calibration_observation(cpu,False)['power_drive_bytes'])

    def test_short_clicks_are_queued_in_order_instead_of_losing_exit(self):
        from lab_runner import LabRunner
        from collections import deque
        r=LabRunner.__new__(LabRunner)
        r.interactive_mode=True;r.front_key_queue=deque();r.held_keys=set();r.tick_wraps=0
        r.key_releases=[];r.power_release=None;r.panel_inputs={0x40010800:0x403};r.PA0=1
        r.adc_dma=SimpleNamespace(profile={'channels':{'8':4095,'9':4095}})
        r.event=lambda *args,**kwargs:None
        for keys in (['MENU'],[],['EXIT'],[]):r.set_keys(keys)
        self.assertEqual(r.held_keys,{'MENU'})
        r.tick_wraps=80;r.drain_front_keys();self.assertEqual(r.held_keys,{'EXIT'})
        r.tick_wraps=160;r.drain_front_keys();self.assertEqual(r.held_keys,set())
        self.assertEqual(len(r.front_key_queue),0)

    def test_LCD_fast_dispatch_preserves_GPIO_edges_and_pixels(self):
        lcd=LcdBus();lcd.armed=True;lcd.pixel_format=0x55;lcd.display_on=True;lcd.sleeping=False
        lcd.columns=(0,0);lcd.rows=(0,0);lcd.width=lcd.height=1;lcd.new_command(0x2C)
        r=SimpleNamespace(lcd=lcd,gpio={0x40010C00:{12:0x800},0x40011800:{12:1}},steps=7)
        for value in (0x12,0x34):
            self.assertTrue(fast_lcd_gpio(r,0x180C,4,(value<<7)|1))
            self.assertTrue(fast_lcd_gpio(r,0xC14,4,0x400))
            self.assertTrue(fast_lcd_gpio(r,0xC10,4,0x400))
        self.assertEqual(lcd.pixels[(0,0)],0x1234)
        self.assertEqual(lcd.write_edges,2)
        self.assertEqual(r.gpio[0x40011800][12]&1,1)
        self.assertFalse(fast_lcd_gpio(r,0xC10,4,0x10))
        self.assertFalse(fast_lcd_gpio(r,0x180C,4,0))
        self.assertFalse(fast_lcd_gpio(r,0x180C,2,0))


if __name__=='__main__':unittest.main()
