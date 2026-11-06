"""Host CDC ACM state machine. All descriptors/data come from firmware PMA.

No AnyTone command handler or memory image shortcut exists in this module.
tick() runs in the CPU thread and issues at most one USB transaction per call.
"""
import struct,time,uuid
from collections import deque
from emulate_clock_v121 import StopModel


def cdc_configuration(data):
    if len(data)<9 or data[:2]!=b'\x09\x02' or int.from_bytes(data[2:4],'little')!=len(data):
        raise ValueError('Invalid USB configuration descriptor')
    at=0;interfaces={};current=None;union=None
    while at<len(data):
        size=data[at]
        if size<2 or at+size>len(data):raise ValueError('Truncated USB descriptor')
        d=data[at:at+size];kind=d[1]
        if kind==4 and size>=9:
            current=(d[2],d[3]);interfaces[current]=dict(cls=d[5],sub=d[6],endpoints=[])
        elif kind==5 and size>=7 and current is not None:
            interfaces[current]['endpoints'].append((d[2],d[3]&3,int.from_bytes(d[4:6],'little')&2047))
        elif kind==0x24 and size>=5 and d[2]==6:
            union=(d[3],d[4])
        at+=size
    controls=[n for (n,alt),d in interfaces.items() if alt==0 and d['cls']==2 and d['sub']==2]
    if len(controls)!=1:raise ValueError('Exactly one CDC ACM function is supported')
    control=controls[0]
    choices=[(n,d) for (n,alt),d in interfaces.items() if alt==0 and d['cls']==10 and (union is None or union==(control,n))]
    if len(choices)!=1:raise ValueError('CDC data interface missing or ambiguous')
    data_interface,interface=choices[0];bulk=[e for e in interface['endpoints'] if e[1]==2]
    rx=[e for e in bulk if e[0]&128];tx=[e for e in bulk if not e[0]&128]
    if len(rx)!=1 or len(tx)!=1 or any(not 1<=e[2]<=64 for e in bulk):raise ValueError('Unsupported CDC bulk endpoints')
    notifications=[e[0] for e in interfaces[(control,0)]['endpoints'] if e[0]&128 and e[1]==3]
    return dict(configuration=data[5],control_interface=control,data_interface=data_interface,
                bulk_in=rx[0][0],bulk_out=tx[0][0],in_size=rx[0][2],out_size=tx[0][2],notification=notifications[0] if notifications else None)


class CdcHost:
    LIMIT=65536
    def __init__(self,usb,timeout=30):
        self.usb=usb;self.timeout=timeout;self.session=uuid.uuid4().hex
        self.state='disconnected';self.error=None;self.control=None;self.layout=None
        self.outgoing=bytearray();self.received=bytearray();self.received_total=0;self.sent_total=0
        self.log=deque(maxlen=256);self.sequence=0;self.next_poll=0;self.notifications=deque(maxlen=8)
        self.device_descriptor=b'';self.configuration_descriptor=b'';self.ep0_size=8;self.units=0
        self.bulk_phase=0
        self.disconnect_reason=None
    def record(self,kind,**values):
        self.sequence+=1;self.log.append(dict(sequence=self.sequence,virtual_units=self.units,kind=kind,**values))
    def start(self):
        self.disconnect_reason=None
        self.usb.token('CONNECT');self.usb.token('RESET');self.state='enumerating';self.error=None
        self.deadline=time.monotonic()+self.timeout
        self.request('device8',0x80,6,0x100,0,8)
    def close(self):
        self.disconnect_reason='USB_CDC_STOP requested';self.record('disconnected',reason=self.disconnect_reason)
        self.usb.token('DISCONNECT');self.state='disconnected';self.control=None;self.outgoing.clear()
    def request(self,name,kind,request,value,index,length,payload=b''):
        self.control=dict(name=name,setup=struct.pack('<BBHHH',kind,request,value,index,length),
            direction_in=bool(kind&128),length=length,payload=bytes(payload),position=0,data=bytearray(),stage='setup')
        self.deadline=time.monotonic()+self.timeout
        self.record('control_request',name=name,setup=self.control['setup'].hex())
    def queue(self,payload):
        if self.state!='ready':raise ValueError('USB CDC is not ready')
        if not payload or len(self.outgoing)+len(payload)>self.LIMIT:raise ValueError('USB CDC output queue full or empty payload')
        self.outgoing.extend(payload)
    def token(self,kind,endpoint=0,payload=b''):
        result=self.usb.token(kind,endpoint,bytes(payload))
        if result['status']=='STALL':raise ValueError(f'USB endpoint {endpoint} stalled during {kind}')
        return result
    def tick(self,units):
        self.units=units
        if self.state in ('disconnected','error') or units<self.next_poll:return
        self.next_poll=units+2048
        try:
            if self.control:
                if time.monotonic()>self.deadline:raise ValueError('USB control transfer timed out: '+self.control['name']+'/'+self.control['stage'])
                self.control_tick();return
            if self.state!='ready':return
            # Alternate IN and OUT so a busy transmitter cannot starve replies.
            self.bulk_phase^=1
            if self.outgoing and self.bulk_phase:
                data=bytes(self.outgoing[:self.layout['out_size']])
                if self.token('OUT',self.layout['bulk_out']&15,data)['status']=='ACK':
                    del self.outgoing[:len(data)];self.sent_total+=len(data);self.record('bulk_OUT',hex=data.hex())
            else:
                result=self.token('IN',self.layout['bulk_in']&15)
                if result['status']=='ACK':
                    data=bytes.fromhex(result['hex'])
                    self.received.extend(data);self.received_total+=len(data)
                    if len(self.received)>self.LIMIT:del self.received[:-self.LIMIT]
                    self.record('bulk_IN',hex=data.hex())
        except (ValueError,KeyError,struct.error,StopModel) as error:
            self.error=str(error);self.state='error';self.control=None;self.record('error',message=self.error)
    def control_tick(self):
        c=self.control;stage=c['stage']
        if stage=='setup':
            if self.token('SETUP',payload=c['setup'])['status']!='ACK':return
            c['stage']=('in' if c['direction_in'] else 'out') if c['length'] else 'status_in'
        elif stage=='in':
            response=self.token('IN')
            if response['status']!='ACK':return
            data=bytes.fromhex(response['hex']);c['data'].extend(data)
            if len(c['data'])>c['length']:raise ValueError('USB control response exceeds requested length')
            if len(data)<self.ep0_size or len(c['data'])==c['length']:c['stage']='status_out'
        elif stage=='out':
            chunk=c['payload'][c['position']:c['position']+self.ep0_size]
            if self.token('OUT',payload=chunk)['status']!='ACK':return
            c['position']+=len(chunk)
            if c['position']==c['length']:c['stage']='status_in'
        elif stage=='status_out':
            if self.token('OUT')['status']=='ACK':self.complete()
        elif stage=='status_in':
            response=self.token('IN')
            if response['status']=='ACK':
                if response.get('bytes'):raise ValueError('Nonempty control status packet')
                self.complete()
    def complete(self):
        c=self.control;name=c['name'];data=bytes(c['data']);self.control=None
        self.record('control_complete',name=name,hex=data.hex())
        if name=='device8':
            if len(data)!=8 or data[:2]!=b'\x12\x01' or data[7] not in (8,16,32,64):raise ValueError('Invalid device descriptor prefix')
            self.ep0_size=data[7];self.request('address',0,5,1,0,0)
        elif name=='address':
            self.request('device',0x80,6,0x100,0,18)
        elif name=='device':
            if len(data)!=18 or data[:2]!=b'\x12\x01':raise ValueError('Invalid full device descriptor')
            self.device_descriptor=data;self.request('config9',0x80,6,0x200,0,9)
        elif name=='config9':
            if len(data)!=9 or data[:2]!=b'\x09\x02':raise ValueError('Invalid configuration prefix')
            length=int.from_bytes(data[2:4],'little')
            if not 9<=length<=4096:raise ValueError('Configuration too large or invalid')
            self.request('configuration',0x80,6,0x200,0,length)
        elif name=='configuration':
            self.configuration_descriptor=data;self.layout=cdc_configuration(data)
            self.request('configure',0,9,self.layout['configuration'],0,0)
        elif name=='configure':
            self.request('line_coding',0x21,0x20,0,self.layout['control_interface'],7,struct.pack('<IBBB',115200,0,0,8))
        elif name=='line_coding':
            self.request('control_lines',0x21,0x22,3,self.layout['control_interface'],0)
        elif name=='control_lines':
            self.state='ready';self.usb.enumeration_complete=True;self.record('ready',layout=self.layout)
    def describe(self):
        return dict(session=self.session,state=self.state,error=self.error,disconnect_reason=self.disconnect_reason,layout=self.layout,
            transfer=self.control['name']+'/'+self.control['stage'] if self.control else None,
            device_descriptor_hex=self.device_descriptor.hex(),configuration_descriptor_hex=self.configuration_descriptor.hex(),
            queued_bytes=len(self.outgoing),sent_total=self.sent_total,received_total=self.received_total,
            received_base=self.received_total-len(self.received),received_hex=self.received.hex(),
            recent_events=list(self.log),responses_source='executed firmware USB PMA only',CPS_compatibility_verified=False)
