"""GD32 free watchdog: key, protected prescaler/reload, and reset request.

IRC40K is an ideal 40 kHz source; model units are nominal 120 MHz units,
not measured oscillator cycles. Register updates complete immediately.
Expiry is reported as a reset request; this model does not invent a reboot.
"""
from emulate_clock_v121 import StopModel


class FreeWatchdog:
    def __init__(self):
        self.prescaler=0;self.reload=0xFFF;self.unlocked=False
        self.running=False;self.deadline=None;self.expired=False;self.events=[]
    def read(self,offset,size):
        if size not in (2,4) or offset not in (0,4,8,12):raise StopModel('FWDGT register/access not modelled')
        return {0:0,4:self.prescaler,8:self.reload,12:0}[offset]
    def reload_counter(self,now):
        self.deadline=now+(self.reload+1)*(4<<self.prescaler)*3000
    def write(self,offset,size,value,now):
        self.read(offset,size)
        if offset==0:
            if value==0x5555:self.unlocked=True
            elif value==0xCCCC:
                if not self.running:self.running=True;self.reload_counter(now)
            elif value==0xAAAA:
                if self.running:self.reload_counter(now)
            else:self.unlocked=False
        elif offset==4:
            if self.unlocked:
                if value>6:raise StopModel('FWDGT reserved prescaler requested')
                self.prescaler=value
        elif offset==8:
            if self.unlocked:self.reload=value&0xFFF
        else:raise StopModel('FWDGT status register is read-only')
        self.events.append(dict(time=now,offset=offset,value=value))
    def advance(self,now):
        if self.running and now>=self.deadline:self.expired=True
        return self.expired
    def describe(self):
        return dict(running=self.running,prescaler=self.prescaler,reload=self.reload,
            deadline=self.deadline,expired=self.expired,events=self.events[-128:],
            clock='ideal IRC40K; nominal model units',automatic_reboot=False)
