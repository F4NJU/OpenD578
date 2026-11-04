"""PB6/PB7 wire decoder and the RDA5807 sequential write interface.

Only address 10h acknowledges. Read status has no invented station/ready data.
Source: RDA5807M datasheet Rev 1.0, section 2.5 (fixed write start 02h).
"""
from emulate_clock_v121 import StopModel


class FmI2c:
    def __init__(self):
        self.active=False
        self.phase='receive'
        self.bits=[]
        self.command=None
        self.payload=[]
        self.ack=False
        self.registers={}
        self.frames=[]
        self.absent_addresses={}
        self.starts=0
        self.ack_reads=0

    def finish(self,step):
        if self.command is not None:
            address=self.command>>1
            if address==0x10:
                self.frames.append(dict(step=step,command=self.command,payload=self.payload.copy(),
                    bytes_acknowledged=len(self.payload)+1))
                for i in range(0,len(self.payload)-1,2):
                    self.registers[2+i//2]=(self.payload[i]<<8)|self.payload[i+1]
            else:
                self.absent_addresses[address]=self.absent_addresses.get(address,0)+1
        self.active=False

    def gpio(self,before,after,old_mode,new_mode,step):
        old_scl=bool(before&0x80)
        scl=bool(after&0x80)
        old_sda=bool(before&0x40) if old_mode&3 else True
        sda=bool(after&0x40) if new_mode&3 else True
        # A host START/STOP is a driven SDA edge with the clock already high.
        if old_scl and scl and old_mode&3 and new_mode&3 and old_sda!=sda:
            if sda:
                if self.active:self.finish(step)
            else:
                if self.active:self.finish(step)
                self.active=True
                self.phase='receive'
                self.bits=[]
                self.command=None
                self.payload=[]
                self.ack=False
                self.starts+=1
            return
        if not self.active:return
        if not old_scl and scl:
            if self.phase=='receive':
                if not new_mode&3:raise StopModel('FM I2C host released SDA during transmitted byte')
                self.bits.append(int(sda))
                if len(self.bits)==8:
                    value=0
                    for bit in self.bits:value=(value<<1)|bit
                    if self.command is None:
                        self.command=value
                        self.ack=value>>1==0x10
                        if self.ack and value&1:
                            raise StopModel('RDA5807 FM status read outside qualified write-only model')
                    elif self.ack:self.payload.append(value)
                    self.phase='ack_prepare'
            elif self.phase=='ack':self.phase='ack_high'
        elif old_scl and not scl:
            if self.phase=='ack_prepare':self.phase='ack'
            elif self.phase=='ack_high':
                self.phase='receive' if self.ack else 'ignore'
                self.bits=[]

    def input_bit(self):
        if self.active and self.ack and self.phase in ('ack','ack_high'):
            self.ack_reads+=1
            return 0
        return 1

    def describe(self):
        return dict(SDA='PB6',SCL='PB7',model='RDA5807-compatible sequential writes at 7-bit address 10h',
            frames=self.frames,ack_input_reads=self.ack_reads,starts=self.starts,
            absent_address_counts={f'{a:02X}':n for a,n in self.absent_addresses.items()},
            last_written_registers={f'{a:02X}':v for a,v in self.registers.items()},
            read_status_or_RF_simulated=False,physical_device_identified=False)
