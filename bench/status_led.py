"""PE3/PE4 LSB-first board status command, inferred from OEM wire execution.

Bootloader 080042BA sends 8 bits, toggles 00/10 in update mode. Application
RX/idle/TX/idle sends 4E/46/56/46. User observes green RX and red TX.
Bits 3/4 are therefore mapped to green/red with firmware-correlated confidence,
not continuity-measured board wiring. Other bits have no assigned LED meaning.
"""

class StatusLedBus:
    def __init__(self):
        self.bits=[];self.frames=[];self.value=None;self.total_frames=0

    def gpio(self,before,after,mode,step):
        if not all((mode>>(4*n))&3 for n in (3,4)):
            self.bits.clear();return
        if not before&16 and after&16:
            self.bits.append(1 if after&8 else 0)
            if len(self.bits)==8:
                self.value=sum(b<<i for i,b in enumerate(self.bits));self.bits.clear()
                self.total_frames+=1;self.frames.append(dict(step=step,value=self.value))
                if len(self.frames)>64:del self.frames[:-64]

    def describe(self):
        red=None if self.value is None else bool(self.value&16)
        green=None if self.value is None else bool(self.value&8)
        state='unknown' if red is None else 'red+green' if red and green else 'red' if red else 'green' if green else 'off'
        return dict(state=state,red=red,green=green,raw_command=self.value,
            source='PE3 data / PE4 rising clock edges, 8 bits LSB first',
            decoded=self.value is not None,physical_mapping_verified=False,
            mapping_confidence='firmware_correlated_with_user_observation',
            red_mask=16,green_mask=8,other_bits_unassigned=True,
            frames=self.frames,total_frames=self.total_frames,pending_bits=len(self.bits))
