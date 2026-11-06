"""GPIO Intel HPI and a documented SCT3258 boot handshake subset.

This is a protocol model, not execution of the DSP/vocoder firmware. Unknown
packets stop with their complete wire bytes instead of an unconditional OK.
"""
from collections import deque
import hashlib
from emulate_clock_v121 import StopModel


class SctHpi:
    # Fixed writable control field lengths, including the identifier. Packet
    # Interface v1.0, table 1-5. Event/voice/identity and variable fields excluded.
    CONTROL_LENGTHS={0x02:2,0x05:3,0x06:8,0x0A:3,0x10:2,0x12:2,0x15:2,
        0x16:2,0x18:4,0x19:2,0x1A:2,0x1C:3,0x1D:2,0x1F:18,
        0x2C:3,0x2D:2,0x2E:2,0x2F:2,0x39:13,0x3C:12,0x3D:23,0x3E:2,
        0x41:6,0x42:10,0x46:3,0x68:3,0x69:3,0x6B:13,0x6C:13,0x70:12}
    # OEM puts common controls (observed 1Dh and 41h) inside type 5 too.
    DMR_LENGTHS={**CONTROL_LENGTHS,0x36:6,0x50:4,0x51:4,0x6F:2,0x76:4,0x77:2,0x79:6,0x7A:9,0x7D:5,0x7E:5}
    def __init__(self):
        self.armed=False
        self.boot_expected=b''
        self.boot_received=bytearray()
        self.boot_complete=False
        self.rx=deque()
        self.read_latch=None
        self.tx=bytearray()
        self.frames=[]
        self.read_bytes=0
        self.write_bytes=0
        self.controls={}
        self.codec_page=0
        self.codec_writes=[]
        self.firmware_reference=None
        self.empty_read_strobes=0

    def load_reference(self,path):
        data=path.read_bytes()
        expected='d5ada473af891b6c707978f0b9dde81324afcc4af27348d3bcdf70615ab19407'
        if len(data)!=603102 or hashlib.sha256(data).hexdigest()!=expected:
            raise ValueError('Unexpected SCT3258 vendor reference')
        self.firmware_reference=dict(file='SCT3258TD_UpdateFlash_V2_01_07BF.hex',sha256=expected,
            software_version='V2.01.07BF',meaning='configured protocol model identity from authenticated vendor package; not a live radio measurement')

    def start_boot(self,expected):
        self.armed=True
        self.boot_expected=bytes(expected)
        self.boot_received=bytearray()
        self.boot_complete=False
        self.rx.clear()
        self.tx.clear()
        self.read_latch=None

    def packet(self,payload,kind=0x20):
        packet=b'\x84\xa9\x61'+len(payload).to_bytes(2,'big')+bytes([kind])+bytes(payload)
        if len(packet)&1:packet+=b'\x00'
        self.rx.extend(packet)
        self.frames.append(dict(direction='SCT_to_MCU',hex=packet.hex(),source='documented protocol model'))

    def write_byte(self,value):
        self.write_bytes+=1
        if not self.boot_complete:
            self.boot_received.append(value)
            position=len(self.boot_received)-1
            if value!=self.boot_expected[position]:raise StopModel('SCT boot GPIO byte differs from OEM source')
            if len(self.boot_received)==len(self.boot_expected):
                self.boot_complete=True
                self.packet([0x17,1])
            return
        self.tx.append(value)
        if len(self.tx)<=3:
            if self.tx!=b'\x84\xa9\x61'[:len(self.tx)]:raise StopModel('SCT HPI packet has invalid header')
        if len(self.tx)>=6:
            size=6+int.from_bytes(self.tx[3:5],'big')
            size+=(size&1)
            if len(self.tx)==size:
                packet=bytes(self.tx)
                self.process_packet(packet)
                self.tx.clear()

    def process_packet(self,packet):
        kind=packet[5]
        payload=packet[6:6+int.from_bytes(packet[3:5],'big')]
        if kind==0x23 and payload==b'\x32' and self.firmware_reference:
            value=self.firmware_reference['software_version'].encode('ascii')
            self.frames.append(dict(direction='MCU_to_SCT',hex=packet.hex(),source='OEM software-version query'))
            self.packet(bytes([0x32,len(value)])+value,kind)
            return
        if kind==0x40 and self.controls.get(0x2D)==b'\x01' and payload and not len(payload)&1:
            for position in range(0,len(payload),2):
                address,value=payload[position:position+2]
                if address>127:raise StopModel('AIC3204 codec write address outside seven-bit register file')
                if address==0:
                    if value not in (0,1):raise StopModel('AIC3204 codec page outside qualified controls')
                    self.codec_page=value
                self.codec_writes.append(dict(page=self.codec_page,register=address,value=value))
            self.frames.append(dict(direction='MCU_to_SCT',hex=packet.hex(),source='OEM codec bypass packet'))
            self.packet([0x17,0],0x40)
            return
        lengths=self.CONTROL_LENGTHS if kind==0 else self.DMR_LENGTHS if kind==5 else {}
        fields=[]
        position=0
        while position<len(payload):
            field=payload[position]
            count=lengths.get(field)
            if count is None or position+count>len(payload):break
            value=payload[position+1:position+count]
            if field==0x2D and value[0] not in (1,2,3):break
            if field==0x10 and value[0] not in (4,16):break
            if field==0x16 and value!=b'\x00':break  # parity-enabled wire format not yet modelled
            fields.append((field,value))
            position+=count
        if fields and position==len(payload):
            for field,value in fields:self.controls[field]=value
            self.frames.append(dict(direction='MCU_to_SCT',hex=packet.hex(),source='OEM HPI GPIO writes'))
            self.packet([fields[-1][0],0],kind)
            return
        raise StopModel('SCT3258 packet outside qualified controls: '+packet.hex(' '))

    def gpio(self,before,after,upper_mode):
        if not self.armed:return
        # PD2 HCSN, PD3 HWRN, PD4 HRDN, PD8..15 HPIDATA.
        if not before&4 and not after&4:
            if before&0x10 and not after&0x10:
                # OEM 0932DC asserts HRDN before changing the MCU direction.
                # Validate direction at the actual input-register sample.
                if upper_mode==0x88888888:
                    # A control strobe alone is not an MCU data sample. Power
                    # down changes these pins with no subsequent ISTAT read.
                    if self.rx:self.read_latch=self.rx[0]
                    else:self.empty_read_strobes=getattr(self,'empty_read_strobes',0)+1
            elif not before&0x10 and after&0x10 and self.read_latch is not None:
                self.rx.popleft()
                self.read_latch=None
                self.read_bytes+=1
            if not before&8 and after&8:
                if upper_mode!=0x33333333:raise StopModel('SCT HPI write data bus not driven')
                self.write_byte((after>>8)&255)

    def input_data(self,levels=None):
        if self.read_latch is None and levels is not None and not levels&0x14 and self.rx:
            self.read_latch=self.rx[0]
        if self.read_latch is None:raise StopModel('SCT HPI data sampled outside read strobe')
        return self.read_latch<<8

    def status(self):return 0 if self.rx else 0x20

    def describe(self):
        return dict(model='SCT3258 documented HPI boot handshake',boot_bytes_received=len(self.boot_received),
            boot_matches_OEM_GPIO_source=self.boot_complete,read_bytes=self.read_bytes,write_bytes=self.write_bytes,
            frames=self.frames,controls={f'{key:02X}':bytes(value).hex() for key,value in self.controls.items()},
            codec_configuration_writes=self.codec_writes,firmware_reference=self.firmware_reference,
            DSP_or_AMBE_firmware_executed=False,RF_or_audio_simulated=False,
            empty_read_strobes=getattr(self,'empty_read_strobes',0),
            pins=dict(HCSN='PD2',HWRN='PD3',HRDN='PD4',HOBIB='PD5',DATA='PD8..PD15'))
