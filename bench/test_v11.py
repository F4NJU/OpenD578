import collections,copy,hashlib,io,pathlib,pickle,unittest
from types import SimpleNamespace
from unittest.mock import patch
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R1,UC_ARM_REG_R2
from memory_watch import MemoryWatch,parse_range
from ready_session import SessionUnpickler
from firmware_profile import HOOKS,inspect_profile
from qualification import assess
from compare_engines import compare

class WindowsPathRecord:
    def __reduce__(self):return pathlib.WindowsPath,('C:/recorded/state',)

class UnsupportedRecord:
    def __reduce__(self):return eval,('40+2',)

def FM_result():
    return dict(stop=dict(kind='instruction_budget'),
        hardware=dict(OEM_state_interpretation_qualified=True,NAND=dict(erases=0,programs=0),Flash=dict(erases=0,programs=0)),
        lcd=dict(command_crosscheck_mismatches=[]),remaining_scenario_events=0,
        hardware_events=[dict(step=0,kind='RF_RX_external_status',bank=0,carrier=True),
            dict(step=1,kind='RX_OEM_state',carrier_gate_A=True,audio_gate_A=True),
            dict(step=2,kind='RF_RX_external_status',bank=0,carrier=False),
            dict(step=3,kind='RX_OEM_state',carrier_gate_A=False,audio_gate_A=False)])

class QualificationRegressionTests(unittest.TestCase):
    def test_complete_FM_sequence_passes(self):
        self.assertEqual(assess('FM',FM_result())['status'],'passed')
    def test_old_closed_state_before_withdrawal_does_not_pass(self):
        r=FM_result();r['hardware_events'][-2],r['hardware_events'][-1]=r['hardware_events'][-1],r['hardware_events'][-2]
        for step,event in enumerate(r['hardware_events']):event['step']=step
        self.assertEqual(assess('FM',r)['status'],'failed')
    def test_unqualified_image_does_not_pass_with_correct_pixels_and_RAM(self):
        r=FM_result();r['hardware']['OEM_state_interpretation_qualified']=False
        self.assertEqual(assess('FM',r)['status'],'incomplete')
    def test_silent_NAND_program_fails_functional_scenario(self):
        r=FM_result();r['hardware']['NAND']['programs']=1
        self.assertEqual(assess('FM',r)['status'],'failed')
    def test_LCD_bus_disagreement_fails(self):
        r=FM_result();r['lcd']['command_crosscheck_mismatches']=[dict(expected=42,actual=43)]
        self.assertEqual(assess('FM',r)['status'],'failed')
    def test_incomplete_stimuli_do_not_pass(self):
        r=FM_result();r['remaining_scenario_events']=1
        self.assertEqual(assess('FM',r)['status'],'incomplete')
    def test_empty_history_is_incomplete_instead_of_crashing(self):
        r=FM_result();r['hardware_events']=[]
        self.assertEqual(assess('FM',r)['status'],'incomplete')
    def test_lost_history_is_incomplete(self):
        r=FM_result();r['hardware_event_counts']={'RX_OEM_state':3}
        self.assertEqual(assess('FM',r)['status'],'incomplete')
    def test_receive_overrun_fails(self):
        r=FM_result();r['usart1']={'overruns':1}
        self.assertEqual(assess('FM',r)['status'],'failed')

class PortableSessionTests(unittest.TestCase):
    def test_original_windows_path_record_is_loadable_on_this_host(self):
        data=pickle.dumps(dict(path=WindowsPathRecord(),counts=collections.Counter(a=1),queue=collections.deque([1,2])))
        value=SessionUnpickler(io.BytesIO(data)).load()
        self.assertIsInstance(value['path'],pathlib.Path)
        self.assertEqual(value['counts']['a'],1)
        self.assertEqual(list(value['queue']),[1,2])
    def test_unexpected_recorded_class_is_rejected(self):
        with self.assertRaises(pickle.UnpicklingError):SessionUnpickler(io.BytesIO(pickle.dumps(UnsupportedRecord()))).load()

class MemoryWatchTests(unittest.TestCase):
    def test_cpu_and_model_accesses_are_both_observed(self):
        cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB);cpu.mem_map(0x1000,4096);cpu.mem_map(0x20000000,4096)
        cpu.mem_write(0x1000,bytes.fromhex('08681060')) # ldr r0,[r1]; str r0,[r2]
        runner=SimpleNamespace(cpu=cpu,steps=0,adc_dma=SimpleNamespace(write_memory=cpu.mem_write))
        cpu.hook_add(UC_HOOK_CODE,lambda *args:setattr(runner,'steps',runner.steps+1))
        watch=MemoryWatch(runner,[(0x20000004,8)])
        runner.adc_dma.write_memory(0x20000004,b'abcd')
        cpu.reg_write(UC_ARM_REG_R1,0x20000004);cpu.reg_write(UC_ARM_REG_R2,0x20000008)
        cpu.emu_start(0x1001,0x1004)
        report=watch.describe();r=report['ranges'][0]
        self.assertEqual(cpu.mem_read(0x20000008,4),b'abcd')
        self.assertEqual((r['CPU_reads'],r['CPU_writes'],r['model_writes']),(1,1,1))
        self.assertEqual((r['bytes_read'],r['bytes_written']),(4,8))
        self.assertFalse(report['SRAM_proven_free'])
    def test_invalid_watch_never_extends_outside_SRAM(self):
        for text in ('0x20000000:0','0x1FFFFFFF:8','0x20017FFF:2','bad'):
            with self.assertRaises(ValueError):parse_range(text)

class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.data=bytes(max(HOOKS)-0x08006000+16)
        self.guard=patch('firmware_profile.EXPECTED_SHA',hashlib.sha256(self.data).hexdigest());self.guard.start()
        self.addCleanup(self.guard.stop)
    def test_changed_GPS_observer_is_detected_before_execution(self):
        changed=bytearray(self.data);changed[0x0806CD02-0x08006000]=1
        report=inspect_profile(self.data,changed)
        self.assertFalse(report['anchors_compatible'])
        self.assertEqual(report['mismatches'][0]['address'],'0x806cd02')
    def test_matching_anchors_do_not_certify_changed_application_ABI(self):
        changed=bytearray(self.data);changed[32]=1
        report=inspect_profile(self.data,changed)
        self.assertTrue(report['anchors_compatible']);self.assertFalse(report['OEM_RAM_ABI_qualified'])
        self.assertFalse(report['modified_firmware_certified'])

class DifferentialTests(unittest.TestCase):
    def test_missing_CPU_evidence_cannot_be_equal_by_default(self):
        r=dict(stop=dict(kind='instruction_budget'))
        self.assertEqual(compare(r,r)['status'],'incomplete')
    def test_identical_RAM_does_not_hide_interrupt_timing_drift(self):
        fields=['firmware_sha256','steps','ram_sha256','cpu_registers','systick','systick_wraps',
            'hardware_configuration','virtual_core_units','remaining_scenario_events','application_running',
            'timers','rtc','RF_control_spi','SCT3258_HPI','usart0','usart1','uart3','flash_cache']
        a={key:0 for key in fields};a.update(stop=dict(kind='instruction_budget'),delivered_exceptions=[dict(step=10)],
            lcd={key:0 for key in ('raw_rgb_sha256','display_on','sleeping','command_crosscheck_mismatches','total_pixel_writes','write_edges','commands')},
            hardware={key:0 for key in ('NAND','Flash','gps_OEM','RX','FAN','power_observation')})
        b=copy.deepcopy(a);b['delivered_exceptions'][0]['step']=18
        report=compare(a,b)
        self.assertEqual(report['status'],'different');self.assertEqual(report['differences'],['delivered_exceptions'])

if __name__=='__main__':unittest.main()
