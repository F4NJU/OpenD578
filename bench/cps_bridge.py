"""Local COM/PTY <-> executed-firmware CDC bridge. Does not implement CPS replies."""
import argparse,json,os,sys,time,urllib.request,urllib.error
from pathlib import Path
from bench_version import APPLICATION,build_id
from web_endpoint import read_endpoint,root_id,loopback_url

ROOT=Path(__file__).resolve().parent


class Client:
    def __init__(self,url=None):
        automatic=not url
        self.url=loopback_url(read_endpoint(ROOT) if automatic else url)
        config=self.get('config')
        if not isinstance(config,dict) or config.get('application')!=APPLICATION or config.get('build_id')!=build_id(ROOT):
            found=config.get('application','serveur inconnu') if isinstance(config,dict) else 'serveur inconnu'
            raise ValueError(f'Serveur incompatible à {self.url} : {found}. Relancer OUVRIR_BANC_WEB depuis le dossier du testeur.')
        if automatic and config.get('root_id')!=root_id(ROOT):raise ValueError('Le serveur détecté appartient à un autre dossier du banc')
        if not config.get('capabilities',{}).get('usb_cdc'):
            raise ValueError(f'Ce serveur ne fournit pas la liaison USB CDC : {self.url}. Relancer la version actuelle du banc.')
        self.server_application=config['application'];self.token=config['token'];self.session=None;self.cursor=0
        self.last_status=None;self.transient_status_reads=0;self.operation='connect'
    def response(self,request):
        url=request if isinstance(request,str) else request.full_url
        try:
            with urllib.request.urlopen(request,timeout=5) as response:return json.load(response)
        except urllib.error.HTTPError as error:
            status=error.code
            try:detail=json.loads(error.read(4096)).get('error','')
            except (OSError,ValueError,AttributeError):detail=''
            error.close()
            hint='Route absente : ancien serveur ou mauvais port.' if status==404 else 'Le serveur a refusé la requête.'
            raise RuntimeError(f'HTTP {status} sur {url}. {hint} {detail}') from error
        except urllib.error.URLError as error:
            raise RuntimeError(f'Serveur inaccessible à {url}. Relancer OUVRIR_BANC_WEB ou vérifier --url.') from error
        except ValueError as error:raise RuntimeError(f'Réponse JSON invalide de {url}') from error
    def get(self,path):
        return self.response(self.url+'/api/'+path)
    def post(self,path,value):
        request=urllib.request.Request(self.url+'/api/'+path,data=json.dumps(value).encode(),headers={'X-Lab-Token':self.token,'Content-Type':'application/json'})
        return self.response(request)
    def cdc_status(self,timeout=5,cursor=None):
        deadline=time.monotonic()+timeout
        while True:
            state=self.get('usb/cdc?view=summary' if cursor is None else 'usb/cdc?cursor='+str(cursor));self.last_status=state
            if not state.get('retryable'):return state
            self.transient_status_reads=getattr(self,'transient_status_reads',0)+1
            if time.monotonic()>=deadline:
                raise RuntimeError('Suivi USB illisible pendant plusieurs secondes : '+str(state.get('error') or state.get('reason')))
            time.sleep(.02)
    def session_error(self,prefix,state):
        reason=state.get('error') or state.get('disconnect_reason') or state.get('reason') or state['state']
        return RuntimeError(f'{prefix}: {reason}; étape={getattr(self,"operation","unknown")}; attendu={self.session}; reçu={state.get("session")}; dernière commande={state.get("last_usb_control")}')
    def diagnostic(self):
        state=getattr(self,'last_status',None) or {}
        fields=('state','error','reason','retryable','disconnect_reason','session','transfer','engine_instance','engine_stop','last_usb_control','last_known_state','last_known_session','sent_total','received_total','queued_bytes','status_source','status_age_seconds')
        return dict(server_url=getattr(self,'url',None),server_application=getattr(self,'server_application',None),operation=getattr(self,'operation',None),
            expected_session=getattr(self,'session',None),transient_status_reads=getattr(self,'transient_status_reads',0),
            USB={k:state[k] for k in fields if k in state})
    def connect(self,timeout=40):
        state=self.cdc_status()
        previous=state.get('session');starting=state['state'] in ('disconnected','error')
        if starting:self.post('usb/start',{})
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            state=self.cdc_status()
            if state['state']=='stopped':raise RuntimeError(state.get('error') or 'Firmware engine stopped')
            if starting and state.get('session')==previous:
                time.sleep(.05);continue
            if state['state']=='ready':
                self.session=state['session'];self.cursor=state['received_total'];self.sent_target=state['sent_total']+state['queued_bytes'];return state
            if state['state'] in ('error','stopped'):raise RuntimeError(state.get('error') or state['state'])
            time.sleep(.05)
        raise TimeoutError('USB CDC enumeration did not finish')
    def write(self,data):
        self.post('usb/write',dict(session=self.session,hex=bytes(data).hex()))
        self.sent_target+=len(data);deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            state=self.cdc_status()
            if state.get('session')!=self.session or state['state']!='ready':raise self.session_error('USB CDC session changed or stopped',state)
            if state['sent_total']>=self.sent_target:return
            time.sleep(.01)
        raise TimeoutError('Firmware did not acknowledge the USB OUT data; not retransmitting')
    def read(self):
        state=self.cdc_status(cursor=self.cursor)
        if state.get('session')!=self.session or state['state']!='ready':raise self.session_error('USB CDC session stopped or changed',state)
        if self.cursor<state['received_base']:raise RuntimeError('USB CDC receive overflow; bytes were not delivered to the CPS')
        data=bytes.fromhex(state['received_hex'])[self.cursor-state['received_base']:]
        self.cursor=state['received_total'];return data
    def exchange(self,data,length,timeout=15):
        self.operation='PROGRAM' if data==b'PROGRAM' else 'identification' if data==b'\x02' else 'memory_read' if data[:1]==b'R' else 'exchange'
        self.write(data);received=bytearray();deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            received.extend(self.read())
            if len(received)==length:return bytes(received)
            if len(received)>length:raise RuntimeError('Unexpected extra USB response bytes; another client may be active')
            time.sleep(.01)
        raise TimeoutError('Firmware response timed out; do not retry writes blindly')
    def prepare(self):
        if self.exchange(b'PROGRAM',3)!=b'QX\x06':raise RuntimeError('Unexpected PROGRAM response from firmware')
        identity=self.exchange(b'\x02',16)
        if identity[:1]!=b'I' or identity[-1]!=6:raise RuntimeError('Invalid radio identification')
        return identity


class PtyPort:
    def __init__(self):
        import pty,tty
        self.master,self.slave=pty.openpty();tty.setraw(self.slave);os.set_blocking(self.master,False)
        self.name=os.ttyname(self.slave)
    def read(self):
        try:return os.read(self.master,4096)
        except BlockingIOError:return b''
    def write(self,data):
        try:return os.write(self.master,data)
        except BlockingIOError:return 0
    def close(self):os.close(self.master);os.close(self.slave)


class SerialPort:
    def __init__(self,name):
        import serial
        self.serial=serial.Serial(name,115200,timeout=0,write_timeout=1)
        self.name=name
    def read(self):return self.serial.read(min(4096,max(1,self.serial.in_waiting)))
    def write(self,data):return self.serial.write(data)
    def close(self):self.serial.close()


def relay_step(client,port,pending,log=None):
    incoming=port.read()
    if incoming:
        client.write(incoming)
        if log:log.write(json.dumps(dict(host_monotonic=time.monotonic(),direction='CPS_to_firmware',hex=incoming.hex()))+'\n');log.flush()
    received=client.read()
    if received:
        pending.extend(received)
        if log:log.write(json.dumps(dict(host_monotonic=time.monotonic(),direction='firmware_to_CPS',hex=received.hex()))+'\n');log.flush()
    if len(pending)>65536:raise RuntimeError('CPS output is blocked; bridge buffer exhausted')
    if pending:
        written=port.write(pending)
        if not 0<=written<=len(pending):raise RuntimeError('Invalid serial write result')
        del pending[:written]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',help='Adresse du banc ; détection du serveur de ce dossier par défaut')
    group=parser.add_mutually_exclusive_group();group.add_argument('--port',help='Bridge end of an existing virtual COM pair, e.g. COM11');group.add_argument('--pty',action='store_true',help='Create a POSIX PTY for the client')
    parser.add_argument('--interactive',action='store_true',help='Ask for the local bench URL and virtual COM port')
    parser.add_argument('--prepare',action='store_true',help='Enter firmware programming mode and identify it before exposing the serial link')
    parser.add_argument('--log',help='Optional private binary-traffic JSONL log')
    args=parser.parse_args()
    if args.interactive:
        args.url=input('Adresse du banc [automatique, même dossier] : ').strip() or args.url
        args.port=input('Port du pont (exemple COM11 ; CPS sur COM10) : ').strip()
    if not args.port and not args.pty:parser.error('Choose --port, --pty or --interactive')
    client=Client(args.url);state=client.connect()
    if args.prepare:
        print('Preparing programming mode through the firmware…',flush=True)
        identity=client.prepare();print('Firmware identity: '+identity[1:8].rstrip(b'\0').decode('ascii',errors='replace'),flush=True)
    port=SerialPort(args.port) if args.port else PtyPort();log=open(args.log,'a',encoding='utf-8') if args.log else None
    print('USB CDC ready. Client port: '+port.name,flush=True)
    print('For a Windows COM pair, select the OTHER end in the CPS.',flush=True)
    pending=bytearray()
    try:
        while True:relay_step(client,port,pending,log);time.sleep(.01)
    except KeyboardInterrupt:pass
    finally:
        port.close()
        if log:log.close()


if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:pass
    except Exception as error:print('Bridge stopped: '+str(error),file=sys.stderr);sys.exit(1)
