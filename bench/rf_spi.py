"""GPIO-level 24-bit AT1846-compatible control bus, limited register model.

Only register 44h (gain/volume, documented reset 00FFh) and explicitly written
control values are used. Dynamic RF status and unknown registers stop explicitly.
Physical chip continuity/variant is not asserted by this digital model.
"""
from emulate_clock_v121 import StopModel


class RfSpi:
    SELECTS=((0x40010C00,0x20),(0x40010C00,4),(0x40011000,0x2000),(0x40011800,2))
    def __init__(self):
        self.armed=False
        self.bank=None
        self.bits=[]
        self.command=None
        self.read_value=None
        self.read_position=0
        self.miso=None
        self.registers={(bank,0,0x44):0x00FF for bank in range(4)}
        self.pages=[0]*4
        self.frames=[]
        self.expected=[]
        self.crosschecks=0
        self.written=set()

    def expect(self,bank,address,value=None):
        self.armed=True
        self.expected.append((bank,address&0x7F,value))

    def selected(self,levels):
        active=[i for i,(port,mask) in enumerate(self.SELECTS) if not levels[port]&mask]
        if len(active)>1:raise StopModel('RF SPI has multiple active chip selects')
        return active[0] if active else None

    def prepare_read(self):
        address=self.command&0x7F
        key=(self.bank,self.pages[self.bank],address)
        idle_inputs={0x0C:0,0x60:0,0x61:0,0x65:127,0x67:0}
        if address in idle_inputs and self.pages[self.bank]==0 and self.bank in (0,1):
            # Explicit synthetic no-carrier/no-audio scenario. Native 0808F932
            # tests 0Ch bit 1 for carrier, 65h[6:0] for noise and 67h[8:0]
            # for received strength. This is an OEM-consumer inference, not an
            # assertion that QA4818N shares every AT1846 register definition.
            self.read_value=getattr(self,'external_inputs',{}).get(self.bank,idle_inputs)[address]
            self.read_position=0
            return
        # Control-register-only scope. Other written addresses may contain
        # hardware-owned bits and must not be treated as arbitrary RAM.
        # V1.21 native read/modify/write consumers: 070812..084C changes only
        # page 1 reg 17h bits 14:8; 51h is another observed control path.
        # Require the precise bank/page and an earlier GPIO write.
        extra=key in getattr(self,'control_readback_keys',()) and key in self.written
        if (address not in (0x44,0x7F) and not extra) or key not in self.registers:
            raise StopModel(f'RF SPI read outside qualified controls: bank {self.bank}, page {self.pages[self.bank]}, register {address:02X}')
        self.read_value=self.registers[key]
        self.read_position=0

    def resume_read_header(self,bank,command):
        self.armed=True
        self.bank=bank
        self.bits=[(command>>bit)&1 for bit in range(7,-1,-1)]
        self.command=command
        self.prepare_read()

    def finish(self,step):
        if self.command is None:raise StopModel('RF SPI incomplete address')
        address=self.command&0x7F
        read=bool(self.command&0x80)
        if read:
            if self.read_position!=16:raise StopModel('RF SPI read did not clock sixteen bits')
            value=self.read_value
        else:
            if len(self.bits)!=24:raise StopModel('RF SPI write did not clock twenty-four bits')
            value=0
            for bit in self.bits[8:]:value=value*2+bit
        page=self.pages[self.bank]
        key=(self.bank,page,address)
        if self.expected:
            bank,reg,wanted=self.expected[0]
            if (bank,reg)!=(self.bank,address) or (wanted is None)!=read or (not read and wanted!=value):
                self.last_mismatch=dict(step=step,expected=dict(bank=bank,register=reg,direction='read' if wanted is None else 'write',value=wanted),
                    actual=dict(bank=self.bank,page=page,register=address,direction='read' if read else 'write',value=value),
                    pending_calls=len(self.expected),recent_frames=self.frames[-8:])
                raise StopModel(f'RF SPI GPIO frame differs from OEM call arguments: expected bank={bank} reg=0x{reg:02X} value={wanted}; actual bank={self.bank} reg=0x{address:02X} value={value}; pending={len(self.expected)}')
            self.expected.pop(0)
            self.crosschecks+=1
        origin=('explicit synthetic receiver/decoder status input' if self.bank in getattr(self,'external_inputs',{}) else 'synthetic no-carrier/no-audio input, inferred OEM register consumers') if address in (0x0C,0x60,0x61,0x65,0x67) else 'previous OEM GPIO write' if key in self.written else 'AT1846S guide reset 44h=00FFh'
        self.frames.append(dict(step=step,bank=self.bank,page=page,register=address,
            direction='read' if read else 'write',value=value,source=origin if read else 'OEM GPIO bits'))
        if not read:
            self.registers[key]=value
            self.written.add(key)
            if address==0x7F:self.pages[self.bank]=value

    def gpio(self,before,after,mode,step):
        if not self.armed:return
        selected=self.selected(after)
        if selected!=self.bank:
            if self.bank is not None:self.finish(step)
            self.bank=selected
            self.bits=[]
            self.command=None
            self.miso=None
            self.read_value=None
        if self.bank is None:return
        if not before[0x40010C00]&8 and after[0x40010C00]&8:
            if self.command is not None and self.command&0x80:
                if mode!=8:raise StopModel('RF SPI receiver SDIO not released with pull-up')
                if self.read_position>=16:raise StopModel('RF SPI excess receive clocks')
                self.miso=(self.read_value>>(15-self.read_position))&1
                self.read_position+=1
            else:
                if mode&3==0:raise StopModel('RF SPI transmitted bit while SDIO is input')
                self.bits.append(1 if after[0x40010C00]&16 else 0)
                if len(self.bits)==8:
                    self.command=0
                    for bit in self.bits:self.command=self.command*2+bit
                    if self.command&0x80:self.prepare_read()

    def input_bit(self):
        if self.bank is None or self.miso is None:raise StopModel('RF SPI input without a qualified read clock')
        return self.miso

    def describe(self):
        result=dict(model='four OEM GPIO radio banks; gain controls and explicit idle inputs',frames=self.frames,
            GPIO_crosschecks=self.crosschecks,registers={f'{b}:{p}:{a:02X}':v for (b,p,a),v in self.registers.items()},
            physical_chip_identified=False,dynamic_RF_or_audio_simulated=False,
            external_input_scenario=dict(name='no carrier, no audio',raw_registers={'0C':0,'60':0,'61':0,'65':127,'67':0},
                interpretation='inferred from OEM consumers; no real RF measurements or chip identity claimed'))
        if getattr(self,'external_inputs',{}):
            result['external_input_scenario']=dict(name='programmable synthetic FM discriminator/CTCSS status',
                raw_registers_by_bank={str(b):{f'{a:02X}':v for a,v in values.items()} for b,values in self.external_inputs.items()},
                interpretation='native OEM consumes status registers; physical RF and waveform decoding are not modelled')
        if getattr(self,'last_mismatch',None):result['last_mismatch']=self.last_mismatch
        return result
