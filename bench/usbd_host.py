"""Digital full-speed USB host tokens for the GD32 single-buffer endpoints.

Models PMA, endpoint handshakes and low-priority interrupts. This does not
implement an AnyTone CPS protocol, a PC USB device, a PHY or DSP transport.
Reference: GD32F30x User Manual, USBD register and buffer descriptor chapters.
"""
from usbd_idle import UsbdIdle
from emulate_clock_v121 import StopModel


class UsbdHost(UsbdIdle):
    def __init__(self,clock_enabled=lambda:True):
        super().__init__()
        self.clock_enabled=clock_enabled
        self.connected=False;self.tokens=[];self.last_response=None
        self.enumeration_complete=False

    def interrupt_flags(self):
        flags=self.regs[0x44]&0x7F00
        for endpoint in range(8):
            value=self.regs[endpoint*4]
            if value&0x8080:
                return flags|0x8000|endpoint|(0x10 if value&0x8000 else 0)
        return flags

    @property
    def irq(self):
        return bool(self.connected and self.clock_enabled() and not self.regs[0x40]&3 and
                    self.interrupt_flags()&self.regs[0x40]&0xFE00)

    def read(self,off,size):
        if off==0x44:
            super().read(off,size)
            return self.interrupt_flags()
        return super().read(off,size)

    def write(self,off,size,value):
        old=self.regs.get(off,0)
        super().write(off,size,value)
        if off<0x20 and self.regs[off]&0x8000:self.regs[off]|=old&0x0800
        if off<0x20 and old&0x8000 and not self.regs[off]&0x8000:
            self.regs[off]&=~0x0800  # Clearing reception CTR clears SETUP too.

    def pma_word(self,address,value=None):
        if address&1 or not 0<=address<=510:raise StopModel('USB PMA logical address outside 512-byte aligned memory')
        if value is None:return self.memory_read(address*2,2)
        self.memory_write(address*2,2,value)

    def table(self,endpoint,field,value=None):
        return self.pma_word(self.regs[0x50]+endpoint*8+field,value)

    def packet_bytes(self,address,count,payload=None):
        if address&1 or count<0 or address+count>512:raise StopModel('USB packet outside PMA')
        if payload is not None:
            for i in range(0,count,2):self.pma_word(address+i,int.from_bytes(payload[i:i+2],'little'))
        else:
            return b''.join(self.pma_word(address+i).to_bytes(2,'little') for i in range(0,count,2))[:count]

    def token(self,kind,endpoint=0,payload=b''):
        if kind=='CONNECT':self.connected=True;response=dict(status='CONNECTED')
        elif kind=='DISCONNECT':self.connected=False;self.enumeration_complete=False;response=dict(status='DISCONNECTED')
        elif kind=='RESET':
            if not self.connected:raise ValueError('Connect the virtual USB host before reset')
            self.enumeration_complete=False
            self.regs[0x44]|=0x400;self.regs[0x4C]=0
            for off in range(0,0x20,4):self.regs[off]&=0x8080
            response=dict(status='RESET')
        else:
            if not self.connected:raise ValueError('Virtual USB host is disconnected')
            if not 0<=endpoint<8:raise ValueError('USB endpoint must be 0..7')
            if kind not in ('SETUP','OUT','IN'):raise ValueError('Unknown USB host token')
            if not self.clock_enabled() or self.regs[0x40]&3 or not self.regs[0x4C]&0x80:
                response=dict(status='DISABLED')
            else:
                # Match the USB endpoint address, not a guessed register slot.
                slots=[n for n in range(8) if self.regs[n*4]&15==endpoint and self.regs[n*4]&0x3030]
                if not slots:
                    response=dict(status='NAK')
                    record=dict(kind=kind,endpoint=endpoint,hex=bytes(payload).hex(),response=response)
                    self.tokens.append(record);self.last_response=response
                    if len(self.tokens)>512:del self.tokens[:-512]
                    return response
                if len(slots)!=1:raise StopModel('USB endpoint mapping ambiguous')
                slot=slots[0];value=self.regs[slot*4]
                endpoint_type=value&0x600
                if (value&0x100 and endpoint_type!=0x200) or endpoint_type==0x400:
                    raise StopModel('USB double-buffered/isochronous endpoint not implemented')
                state=(value>>4)&3 if kind=='IN' else (value>>12)&3
                # GD32F30x UM Rev2.9 §24.4.3: a new SETUP is accepted on
                # configured EP0 even when its normal OUT status is NAK/STALL.
                # Do not overwrite a reception still awaiting firmware service.
                if kind=='SETUP' and endpoint_type==0x200 and state and not value&0x8000:state=3
                if state!=3:response=dict(status=('DISABLED','STALL','NAK')[state])
                elif kind=='OUT' and endpoint_type==0x200 and value&0x100 and payload:
                    response=dict(status='STALL')
                elif kind=='IN':
                    count=self.table(slot,2)&0x3FF
                    if count>64:raise StopModel('USB non-isochronous packet exceeds 64 bytes')
                    data=self.packet_bytes(self.table(slot,0),count)
                    self.regs[slot*4]=((value^0x40)&~0x30)|0x20|0x80
                    response=dict(status='ACK',hex=data.hex(),bytes=len(data))
                else:
                    if kind=='SETUP' and (len(payload)!=8 or value&0x600!=0x200):
                        raise ValueError('SETUP requires eight bytes and a control endpoint')
                    count_config=self.table(slot,6)
                    blocks=(count_config>>10)&31
                    capacity=(blocks+1)*32 if count_config&0x8000 else blocks*2
                    if len(payload)>64 or len(payload)>capacity:
                        raise StopModel('USB OUT/SETUP packet exceeds configured receive buffer')
                    self.packet_bytes(self.table(slot,4),len(payload),payload)
                    self.table(slot,6,(count_config&0xFC00)|len(payload))
                    value=((value^0x4000)&~0x3800)|0x2000|0x8000
                    if kind=='SETUP':value=(value&~0x4030)|0x40|0x20|0x0800
                    self.regs[slot*4]=value
                    response=dict(status='ACK',bytes=len(payload))
        record=dict(kind=kind,endpoint=endpoint,hex=bytes(payload).hex(),response=response)
        self.tokens.append(record);self.last_response=response
        if len(self.tokens)>512:del self.tokens[:-512]
        return response

    def describe(self):
        result=super().describe()
        result.update(scenario='virtual host tokens' if self.connected else 'USB host disconnected',
            host_connected=self.connected,interrupt_pending=self.irq,
            host_packets_injected=len(self.tokens),tokens=self.tokens[-128:],
            last_response=self.last_response,enumeration_simulated=self.enumeration_complete,
            transport='single-buffer control/bulk/interrupt endpoints; PMA and IRQ20',
            CPS_protocol_implemented=False,physical_USB_connection=False)
        return result
