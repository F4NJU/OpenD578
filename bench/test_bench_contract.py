import unittest,tempfile,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from native_gate import NativeGate
from live_io import publish_status
from run_bench import assess
from rf_spi import RfSpi
from bench_runner import BenchRunner

class BenchContractTests(unittest.TestCase):
    def test_quiet_clock_matches_single_instruction_reference(self):
        for divider in (1,8):
            for old in (0,1,8,113):
                for fraction in range(divider):
                    reload=120;distance=(old or reload+1)*divider-fraction
                    for count in (0,1,max(0,distance-1)):
                        if count>=distance:continue
                        value=old;part=fraction
                        for i in range(count):
                            part+=1
                            if part>=divider:part=0;value=value-1 if value else reload
                        r=SimpleNamespace(configuration=True,systick={0x10:5 if divider==1 else 1,0x14:reload,0x18:old},tick_fraction=fraction,steps=0,virtual_units=0,adc_dma=SimpleNamespace(step=0))
                        gate=NativeGate.__new__(NativeGate);gate.r=r;gate.quiet(count)
                        self.assertEqual((r.systick[0x18],r.tick_fraction),(value,part))
    def test_reader_lock_does_not_crash_status_publisher(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'status.json'
            with patch.object(Path,'replace',side_effect=PermissionError),patch('live_io.time.sleep'):
                self.assertFalse(publish_status(path,{'running':True}))
            self.assertTrue(publish_status(path,{'running':False}))
            self.assertFalse(json.loads(path.read_text())['running'])
    def test_receiver_status_is_explicit_and_bank_scoped(self):
        r=BenchRunner.__new__(BenchRunner);r.rx_inputs={};r.rf_spi=RfSpi();r.event=lambda *a,**k:None
        r.input_command(dict(control='RF_RX',bank=0,carrier=True,ctcss='match'))
        self.assertEqual(r.rf_spi.external_inputs[0][0x60],0xC00)
        self.assertNotIn(1,r.rf_spi.external_inputs)
        with self.assertRaises(ValueError):r.input_command(dict(control='RF_RX',bank=2))
    def test_missing_model_never_passes_a_scenario(self):
        result={'stop':{'kind':'DMA engine required'}}
        self.assertEqual(assess('PTT',result)['status'],'incomplete')
    def test_FM_oracle_requires_open_then_closed_audio(self):
        r={'stop':{'kind':'instruction_budget'},'hardware_events':[{'kind':'RX_OEM_state','carrier_gate_A':False,'audio_gate_A':False}]}
        self.assertEqual(assess('FM',r)['status'],'incomplete')
        r['hardware_events'].insert(0,{'kind':'RX_OEM_state','carrier_gate_A':True,'audio_gate_A':True})
        self.assertEqual(assess('FM',r)['status'],'incomplete')
if __name__=='__main__':unittest.main()
