import unittest,tempfile,threading,json,urllib.request,urllib.error,struct,zipfile,time
from pathlib import Path
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from web_server import Laboratory,Handler

class WebServerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name)
        self.lab=Laboratory(root,root,root/'run')
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);self.server.lab=self.lab
        self.url=f'http://127.0.0.1:{self.server.server_port}';self.server.origin=self.url
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.lab.close();self.temp.cleanup()
    def request(self,path,data=None,token=None,origin=None):
        headers={}
        if token:headers['X-Lab-Token']=token
        if origin:headers['Origin']=origin
        return urllib.request.urlopen(urllib.request.Request(self.url+path,data=data,headers=headers),timeout=4)
    def test_running_server_reports_version_and_build(self):
        from bench_version import APPLICATION,VERSION,build_id
        from web_server import ROOT
        with self.request('/api/config') as response:config=json.load(response)
        self.assertEqual(config['application'],APPLICATION)
        self.assertEqual(config['build_id'],build_id(ROOT))
        with self.request('/') as response:html=response.read().decode('utf-8')
        self.assertIn('<title>D578 · Banc '+VERSION+'</title>',html)
        self.assertIn('LABORATOIRE LOCAL · '+VERSION,html)

    def test_native_image_publication_tolerates_a_reader_lock(self):
        from unittest.mock import patch
        from lcd_bus import LcdBus
        lcd=LcdBus();lcd.width=lcd.height=1;lcd.dirty=True
        with patch('lcd_bus.Path.replace',side_effect=PermissionError('reader lock')):
            self.assertFalse(lcd.save(self.lab.run/'locked.png'))
        self.assertTrue(lcd.dirty)

    def test_page_and_assets_are_served(self):
        with self.request('/') as r:self.assertIn(b'D578',r.read())
        with self.request('/app.js') as r:self.assertIn(b'audioGate',r.read())
        with self.request('/cps_link.js') as r:self.assertIn(b'usb/cdc',r.read())
    def test_CDC_writes_are_bound_to_the_running_session(self):
        from types import SimpleNamespace
        self.lab.process=SimpleNamespace(poll=lambda:None)
        (self.lab.run/'usb_cdc.json').write_text(json.dumps(dict(state='ready',session='current')))
        self.lab.cdc_last_status=dict(state='ready',session='current');self.lab.cdc_last_seen=time.monotonic()
        try:
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.request('/api/usb/write',b'{"session":"old","hex":"02"}',self.lab.token)
            self.assertEqual(error.exception.code,400);error.exception.close()
            with patch.object(self.lab,'command',return_value=77) as command:
                with self.request('/api/usb/write',b'{"session":"current","hex":"02"}',self.lab.token) as response:
                    self.assertEqual(json.load(response)['sequence'],77)
                self.assertEqual(command.call_args.args[0],dict(control='USB_CDC_WRITE',hex='02',session='current'))
        finally:self.lab.process=None
    def test_CDC_cursor_reads_only_new_bytes_without_mutating_history(self):
        from types import SimpleNamespace
        self.lab.process=SimpleNamespace(poll=lambda:None)
        self.lab.cdc_last_status=dict(state='ready',session='s',received_base=0,received_total=4,received_hex='41424344')
        self.lab.cdc_last_seen=time.monotonic()
        try:
            with self.request('/api/usb/cdc?cursor=2') as response:value=json.load(response)
            self.assertEqual(value['received_hex'],'4344');self.assertEqual(value['received_base'],2)
            with self.request('/api/usb/cdc?cursor=0') as response:self.assertEqual(json.load(response)['received_hex'],'41424344')
            with self.request('/api/usb/cdc?view=summary') as response:self.assertNotIn('received_hex',json.load(response))
        finally:self.lab.process=None
    def test_mutations_reject_missing_token_and_cross_origin(self):
        for token,origin in [(None,None),(self.lab.token,'https://example.com')]:
            with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/stop',b'{}',token,origin)
            self.assertEqual(error.exception.code,403)
            error.exception.close()
    def test_upload_validates_image_and_keeps_exact_bytes(self):
        image=bytearray(256);struct.pack_into('<II',image,0,0x200170E0,0x08006021)
        with self.request('/api/firmware',bytes(image),self.lab.token,self.url) as r:result=json.load(r)
        self.assertTrue(result['selected']);self.assertEqual(self.lab.selected.read_bytes(),image)
    def test_selected_firmware_forces_reset_with_GPS_and_voltage_at_launch(self):
        source=self.lab.source
        (source/'full_flash_pass1.bin').write_bytes(b'fixture')
        with zipfile.ZipFile(source/'AT-D578 PRO PC SOFTWARE.zip','w') as z:
            z.writestr('SCT3258TD_UpdateFlash_V2_01_07BF.hex',b'fixture')
        with zipfile.ZipFile(source/'D578_PASSATION_PHASE47_NAND_COMPLETE_2026-11-03.zip','w') as z:
            for name in ['nand_main_256MiB.bin','nand_oob64_8MiB.bin','nand_ecc_status_128KiB.bin']:
                z.writestr(name,b'fixture')
        file=source/'chosen.bin';image=bytearray(256);struct.pack_into('<II',image,0,0x200170E0,0x08006021);file.write_bytes(image);self.lab.selected=file
        class Process:
            returncode=0
            def poll(self):return 0
        with patch('web_server.subprocess.Popen',return_value=Process()) as start:
            self.lab.start(dict(boot='ready',firmware='selected',voltage=13.8,gps=dict(mode='fix',latitude=48,longitude=2,rate=4)))
        args=start.call_args.args[0]
        self.assertNotIn('--resume-ready',args);self.assertIn('--firmware',args)
        self.assertEqual(args[args.index('--voltage')+1],'13.8');self.assertEqual(args[args.index('--gps')+1],'fix')

    def test_hardware_worker_runs_and_stops_without_OEM_inputs(self):
        from contract_firmware import build
        file=self.lab.source/'independent.bin';file.write_bytes(build());self.lab.selected=file
        result=self.lab.start(dict(model='hardware',nand='blank',firmware='selected',engine='interactive',coverage=True))
        self.assertEqual(result['model'],'hardware')
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            state=self.lab.status()
            if state.get('steps',0)>20000:break
            time.sleep(.03)
        self.assertEqual(state.get('mode'),'hardware',state)
        self.assertGreater(state['steps'],20000)
        self.assertEqual(state['hardware']['LCD']['display_on'],True)
        self.assertGreater(state['hardware']['coverage']['unique_block_entries'],0)
        self.lab.stop();self.lab.process.wait(timeout=5)
        self.assertEqual(self.lab.process.returncode,0)
        report=json.loads((self.lab.run/'resultat.json').read_text())
        self.assertEqual(report['stop']['kind'],'stopped by simulator user')
        self.assertFalse(report['OEM_PC_hooks'])
if __name__=='__main__':unittest.main()
