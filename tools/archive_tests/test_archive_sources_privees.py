import functools
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.machinery import SourceFileLoader

SRC=Path(__file__).resolve().parents[1]/'archive_sources_privees.py'
a=SourceFileLoader('archiver',str(SRC)).load_module()

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*a):pass

class ArchiveTest(unittest.TestCase):
    def test_local_pages_images_and_original_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)
            webroot=base/'served'; webroot.mkdir()
            (webroot/'index.html').write_text('<h1>Hi</h1><a href="page-2.htm">next</a><img src="pic.png"><link rel="stylesheet" href="screen.css"><a href="file.pdf">pdf</a>',encoding='utf-8')
            (webroot/'page-2.htm').write_bytes(b'<h2>second</h2><img src="pic.png">')
            (webroot/'pic.png').write_bytes(b'photo-byte-content')
            (webroot/'file.pdf').write_bytes(b'%PDF-1.4')
            (webroot/'screen.css').write_text('body {background-image: url(pic.png)}',encoding='utf-8')
            server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(webroot)))
            t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
            try:
                port=server.server_address[1]
                seed=f'http://127.0.0.1:{port}/index.html'
                profile='__test_private__'
                a.SOURCES[profile]={'seeds':[seed],'hosts':{'127.0.0.1'},'crawl_pages':True}
                output=base/'backup'
                crawler=a.PrivateArchive(output,profile,timeout=3,delay=0,max_pages=5,max_assets=10)
                count=crawler.run()
                self.assertEqual(count,5)
                rows=json.loads((output/'manifest.json').read_text('utf-8'))['entries']
                self.assertTrue(all(x.get('status')==200 for x in rows))
                photo=output/'originals'/'127.0.0.1'/'pic.png'
                self.assertEqual(photo.read_bytes(),b'photo-byte-content')
                sha=hashlib.sha256(photo.read_bytes()).hexdigest()
                self.assertIn(sha,(output/'checksum.sha256').read_text('utf-8'))
                original=(output/'originals'/'127.0.0.1'/'index.html').read_text('utf-8')
                offline=(output/'offline'/'127.0.0.1'/'index.html').read_text('utf-8')
                self.assertIn('src="pic.png"',original)
                self.assertIn('src="../../originals/127.0.0.1/pic.png"',offline)
                self.assertTrue((output/'index.html').exists())
            finally:
                server.shutdown(); server.server_close()

    def test_unavailable_seed_creates_report(self):
        with tempfile.TemporaryDirectory() as d:
            profile='__test_failed__'
            a.SOURCES[profile]={'seeds':['http://127.0.0.1:1/index.html'],'hosts':{'127.0.0.1'},'crawl_pages':False}
            crawler=a.PrivateArchive(Path(d),profile,timeout=0.3,delay=0)
            self.assertEqual(crawler.run(),0)
            self.assertEqual(crawler.manifest[0]['status'],'ERROR')
            self.assertTrue((Path(d)/'manifest.json').exists())

if __name__=='__main__':unittest.main()
