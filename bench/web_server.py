"""Loopback-only web faceplate for the existing local Unicorn process."""
import argparse,json,secrets,subprocess,sys,threading,time,webbrowser,hashlib,base64,re,wave,os
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
from firmware_input import inspect_image
from prepare_inputs import check_inputs
from bench_version import APPLICATION, build_id

ROOT=Path(__file__).resolve().parent
STARTUP_BUILD_ID=build_id(ROOT)
class Laboratory:
    def __init__(self,source,cache,run):
        self.source=source;self.cache=cache;self.run=run;self.run.mkdir(parents=True,exist_ok=True)
        if source==Path.home()/'Downloads/D578':
            try:
                remembered=json.loads((ROOT/'work/source_location.json').read_text(encoding='utf-8'))
                candidate=Path(remembered['source'])
                if candidate.is_dir():self.source=candidate
            except (OSError,ValueError,TypeError,KeyError):pass
        self.process=None;self.log=None;self.lock=threading.RLock();self.token=secrets.token_urlsafe(32)
        self.selected=None;self.started=None;self.sequence=0
        self.cdc_last_status=None;self.cdc_start_requested=False;self.last_usb_control=None
        self.engine_instance=secrets.token_hex(8)
        self.cdc_lock=threading.Lock();self.cdc_last_seen=None;self.cdc_channel_error=None;self.reader_thread=None
        self.audio_lock=threading.Lock()
    def cdc_status(self):
        context=dict(engine_instance=self.engine_instance,last_usb_control=self.last_usb_control)
        if not self.process or self.process.poll() is not None:
            state=self.status()
            return dict(context,state='stopped',error=state.get('error') or 'Le moteur est arrêté',engine_stop=state.get('stop'))
        with self.cdc_lock:
            value=self.cdc_last_status;last_seen=self.cdc_last_seen;error=self.cdc_channel_error
        age=time.monotonic()-last_seen if last_seen is not None else None
        if value is not None and not error and age is not None and age<5:
            return dict(value,**context,status_source='worker_pipe_memory',status_age_seconds=round(age,3))
        if value is None and not self.cdc_start_requested and not error:
            return dict(context,state='disconnected',reason='not_started',status_source='worker_pipe_memory')
        return dict(context,state='unavailable',retryable=True,reason='worker_state_unavailable',
            error=error or 'En attente d’un état récent du moteur USB',status_source='worker_pipe_memory',status_age_seconds=age,
            last_known_state=(value or {}).get('state'),last_known_session=(value or {}).get('session'))
    def accept_worker_line(self,process,instance,line,log):
        from cdc_channel import decode,PREFIX
        if line.startswith(PREFIX):
            try:value=decode(line)
            except (ValueError,TypeError) as error:
                with self.cdc_lock:
                    if process is self.process and instance==self.engine_instance:self.cdc_channel_error=str(error)
                return
            with self.cdc_lock:
                if process is self.process and instance==self.engine_instance:
                    self.cdc_last_status=value;self.cdc_last_seen=time.monotonic();self.cdc_channel_error=None
        else:
            try:log.write(line);log.flush()
            except (OSError,ValueError):pass
    def read_worker_output(self,process,instance,log):
        try:
            for line in process.stdout:self.accept_worker_line(process,instance,line,log)
        except (OSError,ValueError) as error:
            with self.cdc_lock:
                if process is self.process and instance==self.engine_instance:self.cdc_channel_error=str(error)
        finally:
            with self.cdc_lock:
                if process is self.process and instance==self.engine_instance:self.cdc_channel_error='Canal du moteur fermé'
    def status(self):
        with self.lock:
            running=self.process is not None and self.process.poll() is None
            try:data=json.loads((self.run/'status.json').read_text(encoding='utf-8'))
            except (OSError,ValueError):data={}
            if self.process is None:data={}
            elif not running:data['running']=False
            data.update(process_running=running,elapsed_host_seconds=round(time.monotonic()-self.started,1) if self.started else 0)
            if self.process is not None and not running and self.process.returncode and not data.get('stop'):
                data.update(running=False,error='La simulation a rencontré une erreur. Consulter results/web/lancement.log.')
            return data
    def start(self,options):
        with self.lock:
            if self.process is not None and self.process.poll() is None:raise ValueError('Une simulation est déjà en cours')
            source=Path(options.get('source',str(self.source)))
            board=options.get('model','oem')
            if board not in ('oem','hardware'):raise ValueError('Modèle de banc inconnu')
            mode=options.get('boot','ready');engine=options.get('engine','interactive')
            persistence=bool(options.get('persist_nand',False))
            nand_state=self.run/'nand_session.dat'
            if persistence and nand_state.exists() and mode=='ready':mode='application'
            if mode not in ('ready','application','bootloader') or engine not in ('interactive','native','python','audit'):raise ValueError('Mode de démarrage ou de calcul inconnu')
            chosen=options.get('firmware','oem')
            firmware=self.selected if chosen=='selected' else ROOT/'firmwares/D578UV2_GD_V2.08_20240619.CDD' if chosen=='plus' else None
            if chosen not in ('selected','plus','oem'):raise ValueError('Choix de firmware inconnu')
            if chosen=='selected' and not firmware:raise ValueError('Choisir le fichier firmware')
            from lab_inputs import validate_keys,gps_sentences
            keys=sorted(validate_keys(options.get('keys',[])))
            gps=options.get('gps',{});mode_gps=gps.get('mode','absent')
            if mode_gps not in ('absent','no_fix','fix'):raise ValueError('Scénario GPS inconnu')
            latitude=float(gps.get('latitude',48));longitude=float(gps.get('longitude',2));utc=gps.get('utc','2026-11-05T12:00:00');rate=int(gps.get('rate',1))
            gps_sentences(latitude,longitude,utc,mode_gps=='fix')
            if rate not in (1,2,4):raise ValueError('Cadence GPS invalide')
            volts=float(options.get('voltage',13.8))
            if not 5<=volts<=30:raise ValueError('Tension hors plage')
            initial=[]
            if board=='hardware':
                from board_image import inspect_board_image,inspect_upload
                captured=options.get('nand','blank')=='captured'
                reference=None;nand_dir=None
                if captured or firmware is None:
                    from prepare_inputs import prepare
                    check_inputs(source,self.cache)
                    reference,nand_dir=prepare(source,self.cache)
                    if firmware is None:firmware=reference
                raw_address=options.get('load_address','auto')
                address=None if raw_address=='auto' else int(str(raw_address),0)
                vector=None
                if address is None:
                    detected=inspect_upload(firmware);address=detected['load_address'];vector=detected['vector_address']
                if mode=='bootloader':vector=0x08000000
                _,meta=inspect_board_image(firmware,address,vector)
                command=[sys.executable,str(ROOT/'run_hardware.py'),str(firmware),'--load-address',hex(meta['load_address']),
                    '--vector-address',hex(meta['vector_address']),'--out-dir',str(self.run),'--instructions','2000000000',
                    '--control-stdin','--engine','python' if engine in ('python','audit') else 'native']
                if captured:command+=['--nand-dir',str(nand_dir)]
                if reference:
                    # Explicit authenticated component bootstrap, not a hook in
                    # the selected MCU application. A changed DSP boot remains
                    # an explicit protocol boundary.
                    boot=self.cache/'sct_boot_reference.bin'
                    data=reference.read_bytes();offset=0x080F56CC-0x08006000
                    boot.write_bytes(data[offset:offset+2048]);command+=['--sct-boot',str(boot)]
                if options.get('coverage',False):command+=['--coverage']
                if options.get('trace'):command+=['--trace']
                if keys:command+=['--initial-keys',','.join(keys)]
                initial.append(dict(control='GPS',mode=mode_gps,latitude=latitude,longitude=longitude,utc=utc,hertz=rate))
                if options.get('microphone'):initial.append(dict(control='MIC_CONNECT',connected=True))
                if options.get('mic_lock'):initial.append(dict(control='MIC_LOCK',locked=True))
                mode='bootloader' if mode=='bootloader' else 'application'
                firmware_digest=meta['sha256']
            else:
                check_inputs(source,self.cache)
                if firmware:inspect_image(firmware)
                if mode=='ready' and not firmware and not (ROOT/'results/ready/session.pkl.gz').is_file():
                    raise ValueError('La reprise OEM nécessite une session locale authentifiée. Choisir Reset application.')
                command=[sys.executable,str(ROOT/'run_lcd.py'),'--source-dir',str(source),'--cache-dir',str(self.cache),'--out-dir',str(self.run),
                    '--engine','python' if engine=='audit' else 'native' if engine=='interactive' else engine,'--instructions','2000000000','--control-stdin']
                if engine=='interactive':command+=['--interactive','--idle-clock-scale','65536']
                if engine=='audit':command+=['--audit']
                command+=['--trace','full' if options.get('trace') else 'minimal']
                if firmware:command+=['--firmware',str(firmware)]
                if mode=='ready' and not firmware:command+=['--resume-ready']
                elif mode=='bootloader':command+=['--entry','bootloader']
                command+=['--gps',mode_gps,'--latitude',str(latitude),'--longitude',str(longitude),'--gps-utc',utc,'--gps-rate',str(rate),'--voltage',str(volts)]
                if keys:command+=['--initial-keys',','.join(keys)]
                if options.get('microphone'):command+=['--microphone']
                if options.get('mic_lock'):command+=['--mic-lock']
                firmware_digest=inspect_image(firmware)[2]['sha256'] if firmware else None
            if persistence:command+=['--nand-state',str(nand_state)]
            command+=['--cdc-stdio']
            if self.reader_thread:self.reader_thread.join(timeout=2)
            self.cdc_last_status=None;self.cdc_start_requested=False;self.last_usb_control=None
            self.cdc_last_seen=None;self.cdc_channel_error=None
            self.engine_instance=secrets.token_hex(8)
            for name in ['stop.request','status.json','lcd.png']:(self.run/name).unlink(missing_ok=True)
            for path in self.run.glob('input_*.json'):path.unlink()
            if self.log:self.log.close()
            self.log=(self.run/'lancement.log').open('w',encoding='utf-8')
            previous_stdin=getattr(self.process,'stdin',None)
            if previous_stdin:previous_stdin.close()
            self.process=subprocess.Popen(command,stdin=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                env=dict(os.environ,PYTHONIOENCODING='utf-8'),
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
            if getattr(self.process,'stdout',None) is not None:
                self.reader_thread=threading.Thread(target=self.read_worker_output,args=(self.process,self.engine_instance,self.log),daemon=True)
                self.reader_thread.start()
            self.source=source;self.active_model=board;self.started=time.monotonic()
            for value in initial:self.command(value)
            try:
                saved=ROOT/'work/source_location.json';saved.parent.mkdir(parents=True,exist_ok=True)
                saved.write_text(json.dumps(dict(source=str(source.resolve()))),encoding='utf-8')
            except OSError:pass
            return dict(started=True,model=board,boot='application' if firmware and mode=='ready' else mode,firmware_SHA256=firmware_digest)
    def command(self,value):
        allowed={'USB_CDC_START','USB_CDC_STOP','USB_CDC_WRITE','USB_HOST','UART_RX','EVENT','KEY_SET','RELEASE_ALL','POWER','P1','P2','P3','P4','P5','P6','MENU','EXIT','DIAL_PUSH','DIAL_UP','DIAL_DOWN',
                 'MIC_CONNECT','MIC_KEYS','MIC_LOCK','GPS','RF_RX','ADC_RAW','VOLTAGE','VOLUME_A','VOLUME_B','TRACE'}
        if value.get('control') not in allowed:raise ValueError('Commande inconnue')
        with self.lock:
            if not self.process or self.process.poll() is not None:raise ValueError('Démarrer la simulation avant d’appliquer cette entrée')
            self.sequence+=1
            payload=dict(value,_request_id=self.sequence)
            try:
                self.process.stdin.write(json.dumps(payload,ensure_ascii=False)+'\n');self.process.stdin.flush()
            except (OSError,ValueError) as error:raise ValueError('Le moteur ne reçoit plus les commandes') from error
            if value.get('control','').startswith('USB_CDC_'):
                kind=value['control'];self.last_usb_control=dict(control=kind,sequence=self.sequence)
                if kind=='USB_CDC_START':self.cdc_start_requested=True
            return self.sequence
    def stop(self):
        with self.lock:
            if self.process and self.process.poll() is None:
                try:
                    self.process.stdin.write('{"control":"STOP"}\n');self.process.stdin.flush()
                except (OSError,ValueError):(self.run/'stop.request').write_text('stop')
    def close(self):
        self.stop()
        if self.process and self.process.poll() is None:
            try:self.process.wait(timeout=8)
            except subprocess.TimeoutExpired:self.process.terminate();self.process.wait(timeout=5)
        if self.reader_thread:self.reader_thread.join(timeout=2)
        if self.log:self.log.close()
        stream=getattr(self.process,'stdout',None)
        if stream:stream.close()
        stream=getattr(self.process,'stdin',None)
        if stream:stream.close()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send(self,value,status=200,mime='application/json; charset=utf-8'):
        data=value if isinstance(value,bytes) else json.dumps(value,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/cps':
            self.send_response(302);self.send_header('Location','/cps/');self.send_header('Content-Length','0');self.end_headers();return
        if path.startswith('/cps/'):
            from cps_assets import read_cps_asset
            try:data,mime=read_cps_asset(ROOT.parent/'cps'/'dist',path)
            except (ValueError,FileNotFoundError):
                self.send(dict(error='CPS absent ou chemin invalide. Depuis le depot : cd cps puis npm run build.'),404);return
            self.send(data,mime=mime);return
        if path.startswith('/api/audio/'):
            match=re.fullmatch(r'/api/audio/([a-f0-9]{32})/(tx\.sigmf-(?:data|meta)|rx\.sigmf-(?:data|meta)|received\.wav|report\.json)',path)
            if not match:self.send(dict(error='Enregistrement inconnu'),404);return
            file=self.server.lab.run/'audio'/match[1]/match[2]
            try:self.send(file.read_bytes(),mime='audio/wav' if file.suffix=='.wav' else 'application/octet-stream')
            except OSError:self.send(dict(error='Enregistrement absent'),404)
            return
        if path in ('/audio_lab.js','/audio_capture_worklet.js','/cps_link.js','/mini_cps_protocol.js','/mini_cps.js','/qualification.js'):
            self.send((ROOT/'web'/path[1:]).read_bytes(),mime='text/javascript; charset=utf-8');return
        if path=='/api/config':self.send(dict(token=self.server.lab.token,source=str(self.server.lab.source),application=APPLICATION,build_id=STARTUP_BUILD_ID,root_id=hashlib.sha256(str(ROOT.resolve()).encode()).hexdigest()[:16],capabilities=dict(usb_cdc=True)));return
        if path=='/api/qualification/catalog':
            self.send((ROOT/'qualification_data/catalog.json').read_bytes());return
        if path=='/api/status':self.send(self.server.lab.status());return
        if path=='/api/usb/cdc':
            value=self.server.lab.cdc_status();query=parse_qs(urlparse(self.path).query)
            if query.get('view')==['summary']:
                value={k:v for k,v in value.items() if k not in ('received_hex','recent_events')}
            elif 'cursor' in query and 'received_hex' in value:
                try:cursor=int(query['cursor'][0])
                except (ValueError,IndexError):self.send(dict(error='Curseur USB invalide'),400);return
                if not 0<=cursor<=2**63-1:self.send(dict(error='Curseur USB invalide'),400);return
                if value['received_base']<=cursor<=value['received_total']:
                    value=dict(value,received_hex=value['received_hex'][2*(cursor-value['received_base']):],received_base=cursor)
            self.send(value)
            return
        if path=='/api/usb/diagnostic':
            lab=self.server.lab
            self.send(dict(status=lab.cdc_status(),last_worker_state=lab.cdc_last_status,transport='worker stdout pipe / server memory'))
            return
        if path in ('/api/report','/api/inventory'):
            report=self.server.lab.run/('resultat.json' if path=='/api/report' else 'inventory.json')
            try:self.send(report.read_bytes())
            except OSError:self.send(dict(error='Rapport pas encore disponible'),404)
            return
        if path=='/api/lcd':
            if getattr(self.server.lab,'active_model','oem')=='hardware' and not (self.server.lab.run/'lcd.png').exists():
                self.send(dict(error='Le firmware n’a pas encore dessiné de pixels'),404);return
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
                from board_image import inspect_upload
                meta=inspect_upload(file);lab.selected=file
                self.send(dict(selected=True,sha256=meta['sha256'],bytes=meta['bytes'],format=meta['format']));return
            value=json.loads(raw)
            if path in ('/api/usb/start','/api/usb/stop','/api/usb/write'):
                kind={'/api/usb/start':'USB_CDC_START','/api/usb/stop':'USB_CDC_STOP','/api/usb/write':'USB_CDC_WRITE'}[path]
                payload=dict(control=kind)
                if kind=='USB_CDC_WRITE':
                    cdc=lab.cdc_status()
                    if cdc.get('retryable'):raise ValueError('Suivi USB momentanément illisible ; aucune nouvelle commande n’a été mise en file')
                    if cdc.get('state')!='ready':raise ValueError('USB CDC pas encore prêt')
                    if value.get('session')!=cdc.get('session'):raise ValueError('Session USB CDC différente')
                    data=bytes.fromhex(value.get('hex',''))
                    if not 1<=len(data)<=4096:raise ValueError('1 à 4096 octets attendus')
                    payload['hex']=data.hex()
                    payload['session']=cdc['session']
                self.send(dict(queued=True,sequence=lab.command(payload)))
            elif path=='/api/audio/loop':
                from audio_iq import Config,read_wav,run_loop
                if not isinstance(value,dict):raise ValueError('Objet JSON attendu')
                config_values=value.get('config',{})
                if not isinstance(config_values,dict) or set(config_values)-set(Config.__dataclass_fields__):raise ValueError('Configuration audio inconnue')
                config=Config(**config_values).validate()
                mode=value.get('mode','fm');pcm=None;rate=48000
                if mode=='fm':pcm,rate=read_wav(base64.b64decode(value.get('wav_base64',''),validate=True))
                if not lab.audio_lock.acquire(blocking=False):raise ValueError('Un traitement audio est déjà en cours')
                try:report=run_loop(lab.run/'audio',pcm,rate,config,mode,value.get('source','N0CALL'),value.get('information','>OpenD578 I/Q test'))
                finally:lab.audio_lock.release()
                self.send(report)
            elif path=='/api/start':self.send(lab.start(value))
            elif path=='/api/inventory':
                if not lab.selected:raise ValueError('Choisir un fichier firmware avant de lancer l’inventaire')
                from board_image import inspect_board_image,inspect_upload
                from firmware_inventory import inventory
                address=value.get('load_address','auto')
                meta=inspect_upload(lab.selected) if address=='auto' else inspect_board_image(lab.selected,int(address,0))[1]
                data,meta=inspect_board_image(lab.selected,meta['load_address'],meta['vector_address'])
                report=inventory(data,meta['load_address'],meta['vector_address'])
                (lab.run/'inventory.json').write_text(json.dumps(report,indent=2))
                self.send(dict(candidate_entries=len(report['candidate_entries']),literal_candidates=len(report['MMIO_literal_candidates'])))
            elif path=='/api/input':self.send(dict(queued=True,sequence=lab.command(value)))
            elif path=='/api/stop':lab.stop();self.send(dict(stop_requested=True))
            elif path=='/api/shutdown':
                self.send(dict(shutting_down=True));threading.Thread(target=self.server.shutdown,daemon=True).start()
            else:self.send(dict(error='Action inconnue'),404)
        except (ValueError,OSError,KeyError,TypeError,EOFError,wave.Error) as error:self.send(dict(error=str(error)),400)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);parser.add_argument('--open-browser',action='store_true')
    parser.add_argument('--source-dir',type=Path,default=Path.home()/'Downloads/D578');parser.add_argument('--cache-dir',type=Path,default=ROOT/'work/inputs')
    parser.add_argument('--out-dir',type=Path,default=ROOT/'results/web');args=parser.parse_args()
    lab=Laboratory(args.source_dir,args.cache_dir,args.out_dir);server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    server.lab=lab;server.origin=f'http://127.0.0.1:{server.server_port}'
    from web_endpoint import record_endpoint
    record_endpoint(ROOT,server.origin,STARTUP_BUILD_ID)
    print(server.origin,flush=True)
    if args.open_browser:webbrowser.open(server.origin)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:lab.close();server.server_close()
if __name__=='__main__':main()

