"""Execute original Thumb programs against the hardware-only model."""
import struct,unittest,json
from pathlib import Path
from hardware_runner import HardwareRunner,BlankNand
from contract_firmware import build
from adc_dma import validate_profile
from unicorn.arm_const import UC_ARM_REG_PC

def make_runner(image=None,base=0x08006000):
    profile=validate_profile(json.loads(Path(__file__).with_name('profiles').joinpath('front_panel.json').read_text()))
    return HardwareRunner(image or build(base),load_address=base,profile=profile)

def sample_word(ram,address):return struct.unpack_from('<I',ram,address-0x20000000)[0]

def radio_bits(ram,address):
    value=0
    for i in range(16):value=(value<<1)|((sample_word(ram,address+4*i)>>4)&1)
    return value

class HardwareFirmwareTests(unittest.TestCase):
    def test_sleep_allowance_renews_after_real_CPU_progress(self):
        image=bytearray(0x108)
        struct.pack_into('<II',image,0,0x20018000,0x08006101)
        struct.pack_into('<I',image,15*4,0x08006105)
        # Genuine thread WFI/branch and SysTick BX LR; no OEM addresses/ABI.
        struct.pack_into('<HHH',image,0x100,0xBF30,0xE7FD,0x4770)
        r=make_runner(bytes(image));r.systick.update({0x10:7,0x14:49999,0x18:49999})
        # A long succession of short scheduled steps must not consume a
        # lifetime quota across interrupts which actually execute instructions.
        r.next_event_delay=lambda:1
        report,_=r.run_hardware(20)
        self.assertEqual(report['stop']['kind'],'instruction_budget')
        self.assertGreater(r.virtual_units,100000)
    def test_non_OEM_image_draws_pixels_and_executes_top_SRAM(self):
        r=make_runner();report,ram=r.run_hardware(12000)
        self.assertEqual(report['stop']['kind'],'instruction_budget')
        self.assertEqual(report['lcd']['total_pixel_writes'],2)
        self.assertEqual(r.lcd.pixels,{(0,0):0xF800,(1,0):0x07E0})
        self.assertEqual(sample_word(ram,0x20017FF4),0x600DC0DE)
        self.assertEqual(sample_word(ram,0x20017FF8),90)
        self.assertEqual(sample_word(ram,0x20017FFC),0xD578CAFE)
        self.assertFalse(report['OEM_PC_hooks']);self.assertFalse(report['OEM_RAM_observers'])
        self.assertEqual(report['minimum_observed_SP'],'0x20017df0')
    def test_code_at_old_NAND_hook_is_ordinary_code(self):
        base=0x08080000;r=make_runner(build(base,0xADBE),base)
        self.assertEqual(r.cpu.reg_read(UC_ARM_REG_PC),0x0808ADBE)
        report,ram=r.run_hardware(12000)
        self.assertEqual(report['stop']['kind'],'instruction_budget')
        self.assertEqual(report['lcd']['total_pixel_writes'],2)
        self.assertEqual(sample_word(ram,0x20017FF4),0x600DC0DE)
    def test_image_at_physical_flash_origin_needs_no_OEM_boot(self):
        r=make_runner(base=0x08000000);report,_=r.run_hardware(12000)
        self.assertEqual(report['stop']['kind'],'instruction_budget')
        self.assertEqual(report['lcd']['total_pixel_writes'],2)
    def test_receiver_bits_are_read_through_GPIO_without_register_mask_heuristic(self):
        for carrier,tone,wanted in [(False,'absent',0),(True,'mismatch',0),(True,'match',0xC00)]:
            with self.subTest(carrier=carrier,tone=tone):
                r=make_runner();r.input_command(dict(control='RF_RX',bank=0,carrier=carrier,ctcss=tone))
                report,ram=r.run_hardware(12000)
                self.assertEqual(report['stop']['kind'],'instruction_budget')
                self.assertEqual(radio_bits(ram,0x20017E00),2 if carrier else 0)
                self.assertEqual(radio_bits(ram,0x20017E40),wanted)
                self.assertEqual(r.rf_spi.registers[(0,0,0x44)],0x1234)
                self.assertEqual(r.rf_spi.crosschecks,0)
    def test_unknown_device_access_is_model_boundary(self):
        image=bytearray(build());struct.pack_into('<II',image,0x200,0xE0014800,0x40013000)
        # ldr r0,=0x40013000; ldr r1,[r0]; b . : unsupported serial register block.
        struct.pack_into('<HH',image,0x208,0x6801,0xE7FE)
        r=make_runner(bytes(image));report,_=r.run_hardware(20)
        self.assertEqual(report['stop']['category'],'model_incomplete')
        self.assertFalse(report['qualified_for_physical_radio'])
    def test_invalid_physical_stack_is_rejected(self):
        image=bytearray(build());struct.pack_into('<I',image,0,0x20020000)
        with self.assertRaises(ValueError):make_runner(bytes(image))
    def test_blank_NAND_has_no_capture_files_and_keeps_one_way_programming(self):
        n=BlankNand();n.features[0xA0]=0
        for command in ([6],[2,0,0,0xAA],[0x10,0,0,0],[6],[2,0,0,0x55],[0x10,0,0,0]):
            n.input_bytes=command;n.end()
        self.assertEqual(n.page_image(0)[0],0)
        self.assertFalse(n.handles)
        self.assertEqual(len(n.program_operations),2)

if __name__=='__main__':unittest.main()
