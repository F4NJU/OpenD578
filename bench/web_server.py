"""Loopback-only web faceplate for the existing local Unicorn process."""
import argparse,json,secrets,subprocess,sys,threading,time,webbrowser,hashlib
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
from firmware_input import inspect_image
from prepare_inputs import check_inputs
from bench_version import APPLICATION, build_id

ROOT=Path(__file__).resolve().parent
STARTUP_BUILD_ID=build_id(ROOT)
class Laboratory:
    def __init__(self,source,cache,run):
        self.source=source;self.cache=cache;self.run=run;self.run.mkdir(parents=True,exist_ok=True)
        self.process=None;self.log=None;self.lock=threading.RLock();self.token=secrets.token_urlsafe(32)
        self.selected=None;self.started=None;self.sequence=0
    def status(self):
        with self.lock:
            running=self.process is not None and self.process.poll() is None
            try:data=json.loads((self.run/'status.json').read_text(encoding='utf-8'))
            except (OSError,ValueError):data={}
            if self.process is None:data={}
            elif not running:data['running']=False
            data.update(process_running=running,elapsed_host_seconds=round(time.monotonic()-self.started,1) if self.started else 0)
            if self.process is not None and not running and self.process.returncode:
                data.update(running=False,error='La simulation a rencontré une erreur. Consulter results/web/lancement.log.')
            return data
    def start(self,options):
        with self.lock:
            if self.process is not None and self.process.poll() is None:raise ValueError('Une simulation est déjà en cours')
            source=Path(options.get('source',str(self.source)))
            check_inputs(source, self.cache)
            mode=options.get('boot','ready');engine=options.get('engine','native')
            if mode not in ('ready','application','bootloader') or engine not in ('native','python','audit'):raise ValueError('Mode de démarrage ou de calcul inconnu')
            firmware=self.selected if options.get('firmware')=='selected' else ROOT/'firmwares/D578UV2_GD_V2.08_20240619.CDD' if options.get('firmware')=='plus' else None
            if options.get('firmware')=='selected' and not firmware:raise ValueError('Choisir le fichier firmware')
            if firmware:inspect_image(firmware)
            command=[sys.executable,str(ROOT/'run_lcd.py'),'--source-dir',str(source),'--cache-dir',str(self.cache),'--out-dir',str(self.run),
                     '--engine','python' if engine=='audit' else engine,'--instructions','200000000']
            if engine=='audit':command+=['--audit']
            command+=['--trace','full' if options.get('trace') else 'minimal']
            if firmware:command+=['--firmware',str(firmware)]
            if mode=='ready' and not firmware:command+=['--resume-ready']
            elif mode=='bootloader':command+=['--entry','bootloader']
            from lab_inputs import validate_keys,gps_sentences
            gps=options.get('gps',{});mode_gps=gps.get('mode','absent')
            if mode_gps not in ('absent','no_fix','fix'):raise ValueError('Scénario GPS inconnu')
            latitude=float(gps.get('latitude',48));longitude=float(gps.get('longitude',2));utc=gps.get('utc','2026-11-04T12:00:00');rate=int(gps.get('rate',1))
            gps_sentences(latitude,longitude,utc,mode_gps=='fix')
            if rate not in (1,2,4):raise ValueError('Cadence GPS invalide')
            volts=float(options.get('voltage',13.8))
            if not 5<=volts<=30:raise ValueError('Tension hors plage')
            command+=['--gps',mode_gps,'--latitude',str(latitude),'--longitude',str(longitude),'--gps-utc',utc,'--gps-rate',str(rate),'--voltage',str(volts)]
            keys=sorted(validate_keys(options.get('keys',[])))
            if keys:command+=['--initial-keys',','.join(keys)]
            if options.get('microphone'):command+=['--microphone']
            if options.get('mic_lock'):command+=['--mic-lock']
            for name in ['stop.request','status.json']:
                (self.run/name).unlink(missing_ok=True)
            for path in self.run.glob('input_*.json'):path.unlink()
            if self.log:self.log.close()
            self.log=(self.run/'lancement.log').open('w',encoding='utf-8')
            self.process=subprocess.Popen(command,stdout=self.log,stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
            self.started=time.monotonic()
            return dict(started=True,boot='application' if firmware and mode=='ready' else mode,
                        firmware_SHA256=inspect_image(firmware)[2]['sha256'] if firmware else None)
    def command(self,value):
        allowed={'KEY_SET','RELEASE_ALL','POWER','P1','P2','P3','P4','P5','P6','MENU','EXIT','DIAL_PUSH','DIAL_UP','DIAL_DOWN',
                 'MIC_CONNECT','MIC_KEYS','MIC_LOCK','GPS','RF_RX','ADC_RAW','VOLTAGE','VOLUME_A','VOLUME_B','TRACE'}
        if value.get('control') not in allowed:raise ValueError('Commande inconnue')
        with self.lock:
            if not self.process or self.process.poll() is not None:raise ValueError('Démarrer la simulation avant d’appliquer cette entrée')
            self.sequence+=1;path=self.run/f'input_{time.time_ns()}_{self.sequence}.json'
            temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value),encoding='utf-8');temporary.replace(path)
    def stop(self):
        with self.lock:
            if self.process and self.process.poll() is None:(self.run/'stop.request').write_text('stop')
    def close(self):
        self.stop()
        if self.process and self.process.poll() is None:
            try:self.process.wait(timeout=8)
            except subprocess.TimeoutExpired:self.process.terminate();self.process.wait(timeout=5)
        if self.log:self.log.close()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send(self,value,status=200,mime='application/json; charset=utf-8'):
        data=value if isinstance(value,bytes) else json.dumps(value,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/api/config':self.send(dict(token=self.server.lab.token,source=str(self.server.lab.source),application=APPLICATION,build_id=STARTUP_BUILD_ID,root_id=hashlib.sha256(str(ROOT).encode()).hexdigest()[:16]));return
        if path=='/api/status':self.send(self.server.lab.status());return
        if path=='/api/lcd':
            run=self.server.lab.run/'lcd.png';path=run if self.server.lab.process and run.exists() else ROOT/'results/reference/lcd.png'
            try:self.send(path.read_bytes(),mime='image/png')
            except OSError:self.send(dict(error='Écran en préparation'),404)
            return
        if path in ('/','/app.js','/style.css'):
            name={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}[path]
            mime={'index.html':'text/html; charset=utf-8','app.js':'text/javascript; charset=utf-8','style.css':'text/css; charset=utf-8'}[name]
            self.send((ROOT/'web'/name).read_bytes(),mime=mime);return
        self.send(dict(error='Page inconnue'),404)
    def do_POST(self):
        lab=self.server.lab
        origin=self.headers.get('Origin')
        if self.headers.get('X-Lab-Token')!=lab.token or (origin and origin!=self.server.origin):
            self.send(dict(error='Session locale invalide'),403);return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=4*1024*1024:raise ValueError('Requête trop volumineuse ou vide')
            raw=self.rfile.read(size);path=urlparse(self.path).path
            if path=='/api/firmware':
                folder=ROOT/'work/selected';folder.mkdir(parents=True,exist_ok=True)
                digest=hashlib.sha256(raw).hexdigest();file=folder/(digest+'.bin');file.write_bytes(raw)
                meta=inspect_image(file)[2];lab.selected=file
                self.send(dict(selected=True,sha256=meta['sha256'],bytes=meta['bytes'],format=meta['format']));return
            value=json.loads(raw)
            if path=='/api/start':self.send(lab.start(value))
            elif path=='/api/input':lab.command(value);self.send(dict(queued=True))
            elif path=='/api/stop':lab.stop();self.send(dict(stop_requested=True))
            elif path=='/api/shutdown':
                self.send(dict(shutting_down=True));threading.Thread(target=self.server.shutdown,daemon=True).start()
            else:self.send(dict(error='Action inconnue'),404)
        except (ValueError,OSError,KeyError) as error:self.send(dict(error=str(error)),400)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);parser.add_argument('--open-browser',action='store_true')
    parser.add_argument('--source-dir',type=Path,default=Path.home()/'Downloads/D578');parser.add_argument('--cache-dir',type=Path,default=ROOT/'work/inputs')
    parser.add_argument('--out-dir',type=Path,default=ROOT/'results/web');args=parser.parse_args()
    lab=Laboratory(args.source_dir,args.cache_dir,args.out_dir);server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    server.lab=lab;server.origin=f'http://127.0.0.1:{server.server_port}'
    print(server.origin,flush=True)
    if args.open_browser:webbrowser.open(server.origin)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:lab.close();server.server_close()
if __name__=='__main__':main()
