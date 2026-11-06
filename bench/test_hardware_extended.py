import struct,unittest
from usbd_host import UsbdHost
from emulate_clock_v121 import StopModel
from contract_firmware import Thumb
from test_hardware_runner import make_runner,sample_word


def sleep_image(kind='tick'):
    base=0x08006000;t=Thumb(base+0x200)
    handler=Thumb(base+0x100)
    handler.write(0x20017FF0,0x12345678)
    if kind=='tick':
        handler.write(0xE000E010,0)
        t.write(0xE000E014,100);t.write(0xE000E018,0);t.write(0xE000E010,7)
        exception=15
    elif kind=='usb':
        handler.write(0x40005C00,0x0280) # Clear receive CTR, preserve transmit CTR.
        t.write(0xE000E100,1<<20);exception=36
    else:
        handler.write(0x40010414,1)
        t.write(0xE000E100,1<<6);t.write(0x40010400,1);t.write(0x4001040C,1)
        exception=22
    handler.half(0x4770)
    t.half(0xBF30)
    t.write(0x20017FF4,0x89ABCDEF);t.half(0xE7FE)
    image=bytearray(b'\xFF'*0x400)
    struct.pack_into('<II',image,0,0x20017D00,base+0x201)
    struct.pack_into('<I',image,exception*4,base+0x101)
    image[0x100:0x100+len(handler.data)]=handler.data
    image[0x200:0x200+len(t.data)]=t.data
    return bytes(image)


class ExtendedHardwareTests(unittest.TestCase):
    def test_native_program_at_old_OEM_hook_has_no_profile_gate(self):
        from contract_firmware import build
        base=0x08080000;r=make_runner(build(base,0xADBE),base);r.enable_native()
        d,ram=r.run_hardware(12000)
        self.assertEqual(d['stop']['kind'],'instruction_budget')
        self.assertEqual(sample_word(ram,0x20017FF4),0x600DC0DE)
        self.assertFalse(d['firmware_profile_required'])

    def test_native_ADC_DMA_matches_reference_while_CPU_reads_destination(self):
        t=Thumb(0x08006200)
        for address,value in [(0x40021018,0x200),(0x40021014,1),
            (0x40020010,0x4001244C),(0x40020014,0x20017F80),(0x4002000C,2),(0x40020008,0x25A1),
            (0x40012404,0x100),(0x4001242C,1<<20),(0x40012434,6|(11<<5)),
            (0x40012408,0x103),(0x40012408,0x103)]:t.write(address,value)
        t.constant(0,0x20017F80);t.half(0x6801);t.half(0xE7FD)
        image=bytearray(b'\xFF'*(0x200+len(t.data)));struct.pack_into('<II',image,0,0x20017D00,0x08006201);image[0x200:]=t.data
        states=[]
        for engine in ('python','native'):
            r=make_runner(bytes(image))
            if engine=='native':r.enable_native()
            d,ram=r.run_hardware(20000);states.append((d,ram))
            self.assertEqual(d['stop']['kind'],'instruction_budget')
            self.assertGreater(d['adc_dma']['total_transfers'],10)
        self.assertEqual(states[0][1],states[1][1])
        self.assertEqual(states[0][0]['adc_dma'],states[1][0]['adc_dma'])

    def test_native_and_reference_preserve_board_state(self):
        states=[]
        for engine in ('python','native'):
            r=make_runner()
            if engine=='native':r.enable_native()
            d,ram=r.run_hardware(100000);states.append((d,ram))
        a,b=states
        self.assertEqual(a[1],b[1])
        for key in ('CPU_PC','lcd','radio','nand','adc_dma','serial','SCT','lighting','interrupts','MMIO_counts','virtual_core_units'):
            with self.subTest(key=key):self.assertEqual(a[0][key],b[0][key])

    def test_systick_wakes_wfi_without_skipping_thread_instructions(self):
        for engine in ('python','native'):
            r=make_runner(sleep_image())
            if engine=='native':r.enable_native()
            d,ram=r.run_hardware(1000)
            self.assertEqual(d['stop']['kind'],'instruction_budget')
            self.assertEqual(sample_word(ram,0x20017FF0),0x12345678)
            self.assertEqual(sample_word(ram,0x20017FF4),0x89ABCDEF)
            self.assertGreater(d['virtual_core_units'],d['steps'])

    def test_power_exti_resumes_same_cpu_after_wait(self):
        r=make_runner(sleep_image('power'));r.enable_native()
        d,ram=r.run_hardware(1000)
        self.assertEqual(d['stop']['category'],'waiting')
        self.assertEqual(sample_word(ram,0x20017FF4),0xA5A5A5A5)
        r.input_command(dict(control='KEY_SET',keys=['POWER']))
        d,ram=r.run_hardware(1000)
        self.assertEqual(sample_word(ram,0x20017FF0),0x12345678)
        self.assertEqual(sample_word(ram,0x20017FF4),0x89ABCDEF)

    def test_usb_setup_reaches_native_interrupt_handler(self):
        r=make_runner(sleep_image('usb'));r.enable_native()
        r.clock.regs[0x1C]|=1<<23
        r.usbd.token('CONNECT');r.usbd.write(0x40,2,0x8000);r.usbd.write(0x4C,2,0x80)
        r.usbd.table(0,4,64);r.usbd.table(0,6,0x8400)
        r.usbd.write(0,2,0x3200)
        d,_=r.run_hardware(1000)
        self.assertEqual(d['stop']['category'],'waiting')
        r.input_command(dict(control='USB_HOST',token='SETUP',hex='8006000100001200'))
        d,ram=r.run_hardware(1000)
        self.assertEqual(sample_word(ram,0x20017FF0),0x12345678)
        self.assertEqual(sample_word(ram,0x20017FF4),0x89ABCDEF)
        self.assertFalse(r.usbd.irq)

    def test_CDC_host_reset_wakes_a_sleeping_firmware_via_IRQ20(self):
        r=make_runner(sleep_image('usb'));r.enable_native()
        handler=Thumb(0x08006100);handler.write(0x20017FF0,0x12345678)
        handler.write(0x40005C44,0xFBFF);handler.half(0x4770)
        r.cpu.mem_write(0x08006100,bytes(handler.data))
        r.clock.regs[0x1C]|=1<<23;r.usbd.write(0x40,2,0x8400)
        d,_=r.run_hardware(1000);self.assertEqual(d['stop']['category'],'waiting')
        r.input_command(dict(control='USB_CDC_START'))
        d,ram=r.run_hardware(1000)
        self.assertEqual(sample_word(ram,0x20017FF0),0x12345678)
        self.assertFalse(r.usbd.regs[0x44]&0x400)


class UsbHostTests(unittest.TestCase):
    def ready(self):
        u=UsbdHost();u.token('CONNECT');u.write(0x40,2,0x8400);u.write(0x4C,2,0x80)
        u.table(0,4,64);u.table(0,6,0x8400);u.write(0,2,0x3200)
        return u
    def test_setup_pma_count_irq_and_software_ack(self):
        u=self.ready();payload=bytes.fromhex('8006000100001200')
        self.assertEqual(u.token('SETUP',payload=payload)['status'],'ACK')
        self.assertEqual(u.packet_bytes(64,8),payload)
        self.assertEqual(u.table(0,6)&0x3FF,8)
        self.assertEqual(u.read(0x44,2)&0x801F,0x8010)
        self.assertTrue(u.irq)
        u.write(0,2,0x0280)
        self.assertFalse(u.irq);self.assertFalse(u.regs[0]&0x0800)
    def test_IN_returns_firmware_bytes_then_NAK(self):
        u=self.ready();u.table(0,0,128);u.table(0,2,3);u.packet_bytes(128,3,b'ABC')
        u.write(0,2,0xB230)
        self.assertEqual(u.token('IN'),dict(status='ACK',hex='414243',bytes=3))
        self.assertEqual(u.token('IN')['status'],'NAK')
    def test_reset_raises_bus_event_without_fabricated_descriptor(self):
        u=self.ready();u.token('RESET')
        self.assertTrue(u.read(0x44,2)&0x400);self.assertTrue(u.irq)
        self.assertEqual(u.regs[0x4C],0)
        u.write(0x44,2,0xFBFF);self.assertFalse(u.irq)
    def test_disconnected_or_unsupported_modes_do_not_ack(self):
        u=UsbdHost()
        with self.assertRaises(ValueError):u.token('IN')
        u=self.ready();u.regs[0]=(u.regs[0]&~0x600)|0x100  # bulk double buffer
        with self.assertRaises(StopModel):u.token('OUT',payload=b'A')
    def test_control_status_out_accepts_zero_length_and_rejects_payload(self):
        u=self.ready();u.regs[0]|=0x100
        self.assertEqual(u.token('OUT',payload=b'A')['status'],'STALL')
        self.assertEqual(u.token('OUT')['status'],'ACK')
    def test_new_setup_accepts_control_NAK_without_overwriting_pending_reception(self):
        u=self.ready();u.regs[0]=(u.regs[0]&~0x3000)|0x2000
        self.assertEqual(u.token('SETUP',payload=bytes.fromhex('0005010000000000'))['status'],'ACK')
        first=u.packet_bytes(64,8)
        self.assertEqual(u.token('SETUP',payload=bytes(8))['status'],'NAK')
        self.assertEqual(u.packet_bytes(64,8),first)


class WatchdogTests(unittest.TestCase):
    def test_protected_config_start_feed_and_expiry(self):
        from watchdog import FreeWatchdog
        w=FreeWatchdog();w.write(8,4,1,0)
        self.assertEqual(w.reload,0xFFF)
        w.write(0,4,0x5555,0);w.write(8,4,1,0);w.write(4,4,0,0)
        w.write(0,4,0xCCCC,100)
        self.assertEqual(w.deadline,24100)
        self.assertFalse(w.advance(24099))
        w.write(0,4,0xAAAA,1000);self.assertEqual(w.deadline,25000)
        self.assertTrue(w.advance(25000))
    def test_watchdog_expiry_is_a_reset_request_not_a_firmware_fault(self):
        t=Thumb(0x08006200)
        for offset,value in [(0,0x5555),(8,0),(4,0),(0,0xCCCC)]:t.write(0x40003000+offset,value)
        t.half(0xE7FE)
        image=bytearray(b'\xFF'*(0x200+len(t.data)))
        struct.pack_into('<II',image,0,0x20017D00,0x08006201);image[0x200:]=t.data
        r=make_runner(bytes(image));r.enable_native();d,_=r.run_hardware(20000)
        self.assertEqual(d['stop']['category'],'reset_requested')
        self.assertTrue(d['watchdog']['expired'])
    def test_aircr_reset_preserves_distinction_from_model_boundary(self):
        r=make_runner();r.core_set(0xD0C,4,0x05FA0004)
        self.assertEqual(r.stop['kind'],'software reset requested')


if __name__=='__main__':unittest.main()
