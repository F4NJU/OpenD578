import unittest,tempfile,threading,json,urllib.request,urllib.error,struct,zipfile
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
        from bench_version import APPLICATION,build_id
        from web_server import ROOT
        with self.request('/api/config') as response:config=json.load(response)
        self.assertEqual(config['application'],APPLICATION)
        self.assertEqual(config['build_id'],build_id(ROOT))
        with self.request('/') as response:html=response.read().decode('utf-8')
        self.assertIn('<title>D578 · Banc V11.1</title>',html)
        self.assertIn('LABORATOIRE LOCAL · V11.1',html)

    def test_page_and_assets_are_served(self):
        with self.request('/') as r:self.assertIn(b'D578',r.read())
        with self.request('/app.js') as r:self.assertIn(b'audioGate',r.read())
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
if __name__=='__main__':unittest.main()
