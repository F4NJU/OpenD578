"""External digital GPS and microphone stimuli; never writes firmware RAM."""
from datetime import datetime,timedelta,timezone
from math import isfinite

MIC_SOURCE='https://github.com/jrobertfisher/AT-D578UV-software-mic'
MIC_CODES={**{str(n):n+1 for n in range(10)},'*':11,'#':12,'SUB_AB':13,
           'UP':16,'DOWN':17,'A':26,'B':27,'C':28,'D':29}
FRONT_KEYS={'P1':(8,250),'P2':(8,1000),'P3':(8,2000),'MENU':(8,3000),
            'P4':(9,250),'P5':(9,1000),'P6':(9,2000),'EXIT':(9,3000)}

def validate_keys(keys):
    if not isinstance(keys,(list,tuple,set)) or any(k not in {*FRONT_KEYS,'DIAL_PUSH','POWER'} for k in keys):
        raise ValueError('Touches de façade inconnues')
    keys=set(keys)
    for channel in (8,9):
        if sum(FRONT_KEYS[k][0]==channel for k in keys if k in FRONT_KEYS)>1:
            raise ValueError('Deux touches du même groupe ADC : réseau de résistances non relevé')
    return keys

def microphone_frame(pressed=(),long=False,last_code=0):
    pressed=set(pressed)
    if pressed-({'PTT'}|set(MIC_CODES)):raise ValueError('Unknown microphone key')
    keys=pressed-{'PTT'}
    if len(keys)>1:raise ValueError('Mic protocol has one keypad code per frame; PTT plus one key is supported')
    code=MIC_CODES[next(iter(keys))] if keys else last_code
    return bytes([0x41,int('PTT' in pressed),int(bool(keys)),int(long and bool(keys)),code,0,0,6])

def nmea(body):
    checksum=0
    for value in body.encode('ascii'):checksum^=value
    return f'${body}*{checksum:02X}\r\n'.encode('ascii')

def coordinate(value,latitude):
    value=float(value)
    limit=90 if latitude else 180
    if not isfinite(value) or abs(value)>limit:raise ValueError('Coordonnée GPS hors plage')
    absolute=abs(value);degree=int(absolute);minutes=(absolute-degree)*60
    if round(minutes,4)>=60:degree+=1;minutes=0
    return f'{degree:0{2 if latitude else 3}d}{minutes:07.4f}',('N' if value>=0 else 'S') if latitude else ('E' if value>=0 else 'W')

def gps_sentences(latitude=48.0,longitude=2.0,utc='2026-11-04T12:00:00',fix=True):
    stamp=datetime.fromisoformat(utc)
    if stamp.tzinfo is not None:stamp=stamp.astimezone(timezone.utc)
    lat,ns=coordinate(latitude,True);lon,ew=coordinate(longitude,False)
    time=stamp.strftime('%H%M%S')+f'.{stamp.microsecond//1000:03d}';date=stamp.strftime('%d%m%y')
    rmc=f'GPRMC,{time},{"A" if fix else "V"},{lat},{ns},{lon},{ew},0.00,0.00,{date},,,{"A" if fix else "N"}'
    gga=f'GPGGA,{time},{lat},{ns},{lon},{ew},{1 if fix else 0},{4 if fix else 0:02d},1.0,100.0,M,0.0,M,,'
    gsv='GPGSV,1,1,04,01,45,000,40,02,50,090,42,03,55,180,43,04,60,270,44' if fix else 'GPGSV,1,1,00'
    return nmea(rmc)+nmea(gga)+nmea(gsv)

class MicrophonePeer:
    mode='microphone-captured-protocol'
    def __init__(self):self.transactions=[]
    def consume(self,byte):return b''

class GpsPeer:
    mode='synthetic-PMTK-NMEA'
    def __init__(self):self.transactions=[]
    def consume(self,byte):return b''

class GpsScenario:
    def __init__(self):
        self.mode='absent';self.latitude=48.0;self.longitude=2.0
        self.utc='2026-11-04T12:00:00';self.next_tick=0;self.frames=0
        self.origin_tick=0;self.events=[]
        self.hertz=1
        self.startup_pending=False
    def configure(self,mode,tick=0,latitude=48.0,longitude=2.0,utc='2026-11-04T12:00:00',hertz=1):
        if mode not in ('absent','fix','no_fix'):raise ValueError('Mode GPS inconnu')
        if hertz not in (1,2,4):raise ValueError('Cadence GPS : 1, 2 ou 4 Hz')
        gps_sentences(latitude,longitude,utc,mode=='fix')
        self.startup_pending=mode!='absent' and self.mode=='absent'
        self.mode=mode;self.latitude=float(latitude);self.longitude=float(longitude);self.utc=utc
        self.next_tick=tick;self.origin_tick=tick
        self.hertz=hertz
        self.events.append(dict(mode=mode,tick=tick,latitude=self.latitude,longitude=self.longitude,utc=utc))
    def advance(self,runner):
        device=runner.usart1
        if self.mode=='absent' or runner.tick_wraps<self.next_tick or device.rx_wire or device.received_data is not None:return
        if device.regs[0xC]&0x2004!=0x2004 or not device.clock_enabled():return
        if self.startup_pending:
            runner.schedule_serial(device,nmea('PMTK010,001'))
            self.startup_pending=False;self.next_tick=runner.tick_wraps+200
            return
        # SysTick cadence is a model clock, not measured GNSS wall time.
        milliseconds=max(0,(runner.tick_wraps-self.origin_tick)*5)
        utc=(datetime.fromisoformat(self.utc)+timedelta(milliseconds=milliseconds)).isoformat()
        runner.schedule_serial(device,gps_sentences(self.latitude,self.longitude,utc,self.mode=='fix'))
        self.frames+=1;self.next_tick=runner.tick_wraps+200//self.hertz
    def describe(self):
        return dict(mode=self.mode,synthetic=True,latitude=self.latitude,longitude=self.longitude,
                    initial_UTC=self.utc,sentence_pairs_sent=self.frames,events=self.events,
                    sentence_types=['PMTK010 startup','GPRMC','GPGGA','GPGSV'],synthetic_rate_Hz=self.hertz,fix_written_directly_to_RAM=False)
