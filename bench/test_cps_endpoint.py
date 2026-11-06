"""Exercise discovery against real HTTP servers and reject stale versions before POST."""
import hashlib,json,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from bench_version import APPLICATION
from web_endpoint import record_endpoint,root_id
import cps_bridge

class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.posts=[]
        self.config=dict(application=APPLICATION,build_id='fixture-build',root_id=root_id(self.root),token='fixture',capabilities=dict(usb_cdc=True))
        owner=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                if self.path=='/api/config':value=owner.config;status=200
                elif self.path=='/api/usb/cdc':value=dict(state='disconnected');status=200
                else:value=dict(error='unknown');status=404
                body=json.dumps(value).encode();self.send_response(status);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
            def do_POST(self):owner.posts.append(self.path);self.send_response(500);self.end_headers()
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);self.url=f'http://127.0.0.1:{self.server.server_port}'
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
    def client(self,url=None):
        with patch.object(cps_bridge,'ROOT',self.root),patch.object(cps_bridge,'build_id',return_value='fixture-build'):
            return cps_bridge.Client(url)
    def test_automatic_discovery_uses_actual_random_port(self):
        record_endpoint(self.root,self.url,'fixture-build')
        client=self.client();self.assertEqual(client.url,self.url)
        self.assertEqual(client.get('usb/cdc')['state'],'disconnected');self.assertEqual(self.posts,[])
    def test_old_server_is_rejected_before_programming(self):
        self.config['application']='D578 local bench V11.3';self.config.pop('capabilities')
        with self.assertRaisesRegex(ValueError,'Serveur incompatible'):self.client(self.url)
        self.assertEqual(self.posts,[])
    def test_missing_rendezvous_does_not_fall_back_to_8765(self):
        with self.assertRaisesRegex(ValueError,'Serveur de ce dossier introuvable'):self.client()
        self.assertEqual(self.posts,[])
    def test_other_folder_and_stale_build_are_rejected(self):
        record_endpoint(self.root,self.url,'fixture-build');self.config['root_id']='other-folder'
        with self.assertRaisesRegex(ValueError,'autre dossier'):self.client()
        self.config['root_id']=root_id(self.root);self.config['build_id']='old'
        with self.assertRaisesRegex(ValueError,'Serveur incompatible'):self.client()
        self.assertEqual(self.posts,[])
    def test_404_names_the_failing_request(self):
        client=self.client(self.url)
        with self.assertRaisesRegex(RuntimeError,'HTTP 404 sur '+self.url+'/api/missing'):client.get('missing')
    def test_changed_server_without_CDC_capability_is_rejected(self):
        self.config['capabilities']={}
        with self.assertRaisesRegex(ValueError,'ne fournit pas la liaison USB CDC'):self.client(self.url)

if __name__=='__main__':unittest.main()
