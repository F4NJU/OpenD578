/* GD32F303 early-boot peripherals. Derived from OpenD578 V11.8
 * emulate_clock_v121.py / hardware_runner.py, register-level, no OEM PC hooks.
 * Copyright 2026 OpenD578 contributors, GPL-3.0-or-later.
 * This is not a complete NVIC or cycle-accurate clock/flash model.
 */
export const RCU_BASE = 0x40021000;
export const FMC_BASE = 0x40022000;
export const SCB_BASE = 0xe000e000;
export const BITBAND_RCU = 0x42420000;
const U32 = x => x >>> 0;
const asLane = (address, size) => {
  if (![1, 2, 4].includes(size) || address % size || ((address & 3) + size > 4)) {
    throw new Error(`Acces MMIO non aligne: 0x${address.toString(16)}, ${size} o`);
  }
  return [(address & ~3) >>> 0, (address & 3) * 8, (2 ** (8 * size) - 1) >>> 0];
};

export class BootPeripherals {
  constructor() { this.reset(); }
  reset(vectorAddress = 0x08000000) {
    this.resetRequested=null;
    this.clock = new Map(Object.entries({
      0x00:0x83,0x04:0,0x08:0,0x0c:0,0x10:0,0x14:0x14,
      0x18:0,0x1c:0,0x20:0,0x24:0x0c000000,0x28:0,
      0x2c:0,0xc0:0x80000000}).map(([k,v])=>[Number(k), U32(v)]));
    this.pendingClock = new Map([[0,0],[16,0],[24,0]]);
    this.flashWaitStates = 0;
    this.systick = new Map([[0x10,0],[0x14,0],[0x18,0]]);
    this.scb = new Map([[0xd00,0x410fc241],[0xd04,0],[0xd08,vectorAddress >>> 0],
      [0xd0c,0xfa050000],[0xd10,0],[0xd14,0],[0xd18,0],[0xd1c,0],[0xd20,0],[0xd24,0],[0xd28,0],[0xd2c,0],[0xd30,0],[0xd34,0],[0xd38,0]]);
    this.nvicEnable = [0,0,0];this.nvicPending=[0,0,0];this.nvicPriority=new Map();
    this.unmodelledReads=0;this.unmodelledWrites=0;
    this.tickSamples=0;
  }
  ready(advance=false) {
    let control=this.clock.get(0);
    const cfg=this.clock.get(4);
    for(const [en,rdy] of [[0,1],[16,17],[24,25]]) {
      const sourceOK=(en!==24)||Boolean(control & (1<<((cfg&(1<<16))?17:1)));
      if(!(control & (1<<en)) || !sourceOK)control &= ~(1<<rdy);
      else if((this.pendingClock.get(en)??0)>0){control &= ~(1<<rdy);if(advance)this.pendingClock.set(en,this.pendingClock.get(en)-1);}
      else control |= (1<<rdy);
    }
    this.clock.set(0,U32(control));
    const requested=cfg&3, ready=[1,17,25][requested];
    if(ready!==undefined && (control&(1<<ready)))this.clock.set(4,U32((cfg&~12)|(requested<<2)));
  }
  rcuRead(offset,size){const [word,shift,mask]=asLane(offset,size);
    if(!this.clock.has(word))throw new Error(`RCU lecture non modelisee +0x${word.toString(16)}`);
    this.ready(word===0);return (this.clock.get(word)>>>shift)&mask;
  }
  rcuWrite(offset,size,value){const [word,shift,mask]=asLane(offset,size);
    if(!this.clock.has(word))throw new Error(`RCU ecriture non modelisee +0x${word.toString(16)}`);
    const old=this.clock.get(word), proposed=U32((old & ~(mask<<shift))|((value&mask)<<shift));
    if(word===0){
      const writable=1|(0x1f<<3)|(1<<16)|(1<<18)|(1<<19)|(1<<24);
      let next=U32((old&~writable)|(proposed&writable));
      const src=(this.clock.get(4)>>>2)&3;
      if(src===0)next|=1;
      if(src===2)next|=1<<24;
      if(src===1||(src===2&&(this.clock.get(4)&(1<<16))))next|=1<<16;
      if(old&(1<<16))next=U32((next&~(1<<18))|(old&(1<<18)));
      for(const en of [0,16,24])if(Boolean(old&(1<<en))!==Boolean(next&(1<<en)))this.pendingClock.set(en,0);
      this.clock.set(0,U32(next));
    }else if(word===4){
      let next=U32((proposed&~12)|(old&12));
      if(this.clock.get(0)&(1<<24)){
        const frozen=(0x3f<<16)|(1<<27)|(1<<30);next=U32((next&~frozen)|(old&frozen));
      }
      this.clock.set(4,next);
    }else if(word===0x24){this.clock.set(word,U32((old&0xfc000000&((proposed&0x1000000)?0:0xffffffff))|(proposed&1)));}
    else if(word===8){this.clock.set(8,U32((old&0xff&~((proposed>>>16)&0xff))|(proposed&0x7f00)));}
    else if(word===0xc0)this.clock.set(word,U32((old&0xff000000)|(proposed&0x10001)|((proposed&0x10000)?0x20000:0)));
    else this.clock.set(word,proposed);
    this.ready();
  }
  bitbandDecode(address){
    const off=address-BITBAND_RCU;
    if(off<0||off>=4096||off%4)throw new Error(`RCU bitband hors plage 0x${address.toString(16)}`);
    const byteOff=Math.floor(off/32),word=byteOff&~3,bit=((byteOff&3)*8)+((off%32)/4);
    return [word,bit];
  }
  bitbandRead(address,size){if(size!==4)throw new Error('RCU bitband utilise des mots de 32 bits');
    const [word,bit]=this.bitbandDecode(address);
    if(!this.clock.has(word))throw new Error(`RCU bitband registre non modele +${word.toString(16)}`);
    return (this.rcuRead(word,4)>>>bit)&1;
  }
  bitbandWrite(address,size,value){if(size!==4)throw new Error('RCU bitband utilise des mots de 32 bits');
    const [word,bit]=this.bitbandDecode(address);
    if(!this.clock.has(word))throw new Error(`RCU bitband registre non modele +${word.toString(16)}`);
    const before=this.clock.get(word),next=U32((before&~(1<<bit))|((value&1)<<bit));
    this.rcuWrite(word,4,next);
  }
  _systickRead(word){
    const value=this.systick.get(word);
    if(word===0x10)this.systick.set(word,value&~(1<<16));
    return U32(value);
  }
  scbRead(offset,size){const [word,shift,mask]=asLane(offset,size);let value;
    if(this.systick.has(word))value=this._systickRead(word);
    else if(this.scb.has(word))value=this.scb.get(word);
    else if(word>=0x100&&word<=0x108 && (word&3)===0)value=this.nvicEnable[(word-0x100)/4]??0;
    else if(word>=0x180&&word<=0x188 && (word&3)===0)value=this.nvicEnable[(word-0x180)/4]??0;
    else if(word>=0x200&&word<=0x208 && (word&3)===0)value=this.nvicPending[(word-0x200)/4]??0;
    else if(word>=0x280&&word<=0x288 && (word&3)===0)value=this.nvicPending[(word-0x280)/4]??0;
    else if(word>=0x400&&word<0x500)value=this.nvicPriority.get(word)??0;
    else throw new Error(`SCB/NVIC lecture non modelisee +0x${word.toString(16)}`);
    return (U32(value)>>>shift)&mask;
  }
  scbWrite(offset,size,value){const [word,shift,mask]=asLane(offset,size);
    const apply=(old)=>U32((old&~(mask<<shift))|((value&mask)<<shift));
    if(this.systick.has(word)){
      if(size!==4)throw new Error('SysTick attend une ecriture 32 bits');
      if(word===0x10)this.systick.set(word,U32((this.systick.get(word)&(1<<16))|(value&7)));
      else if(word===0x14)this.systick.set(word,value&0xffffff);
      else {this.systick.set(0x18,0);this.systick.set(0x10,this.systick.get(0x10)&~(1<<16));}
    }else if(word===0xd08)this.scb.set(word,value&0xffffff80);
    else if(word===0xd0c){
      if(((value>>>16)&0xffff)!==0x5fa)throw new Error('AIRCR cle VECTKEY incorrecte');
      if(value&(1<<2))this.resetRequested='software';
      this.scb.set(word,U32(0xfa050000|(value&0x700)));
    }else if(this.scb.has(word))this.scb.set(word,apply(this.scb.get(word)));
    else if(word>=0x100&&word<=0x108){const idx=(word-0x100)/4;this.nvicEnable[idx]=U32((this.nvicEnable[idx]??0)|(value<<shift));}
    else if(word>=0x180&&word<=0x188){const idx=(word-0x180)/4;this.nvicEnable[idx]=U32((this.nvicEnable[idx]??0)&~(value<<shift));}
    else if(word>=0x200&&word<=0x208){const idx=(word-0x200)/4;this.nvicPending[idx]=U32((this.nvicPending[idx]??0)|(value<<shift));}
    else if(word>=0x280&&word<=0x288){const idx=(word-0x280)/4;this.nvicPending[idx]=U32((this.nvicPending[idx]??0)&~(value<<shift));}
    else if(word>=0x400&&word<0x500)this.nvicPriority.set(word,apply(this.nvicPriority.get(word)??0));
    else if(word===0xf00){const irq=value&0x1ff;if(irq>=96)throw new Error('STIR IRQ > 95 hors simulation');this.nvicPending[irq>>>5]|=1<<(irq&31);}
    else throw new Error(`SCB/NVIC ecriture non modelisee +0x${word.toString(16)}`);
  }
  read(address,size){
    if(address>=RCU_BASE&&address<RCU_BASE+0x1000)return this.rcuRead(address-RCU_BASE,size);
    if(address>=FMC_BASE&&address<FMC_BASE+0x1000){if(address!==FMC_BASE||size!==4)throw new Error('FMC registre autre que wait states non modele');return this.flashWaitStates;}
    if(address>=BITBAND_RCU&&address<BITBAND_RCU+4096)return this.bitbandRead(address,size);
    if(address>=SCB_BASE&&address<SCB_BASE+4096)return this.scbRead(address-SCB_BASE,size);
    throw new Error(`Peripherique systeme non modele 0x${address.toString(16)}`);
  }
  write(address,value,size){
    if(address>=RCU_BASE&&address<RCU_BASE+0x1000)return this.rcuWrite(address-RCU_BASE,size,value);
    if(address>=FMC_BASE&&address<FMC_BASE+0x1000){if(address!==FMC_BASE||size!==4)throw new Error('FMC programmation/effacement non modelise');this.flashWaitStates=value&7;return;}
    if(address>=BITBAND_RCU&&address<BITBAND_RCU+4096)return this.bitbandWrite(address,size,value);
    if(address>=SCB_BASE&&address<SCB_BASE+4096)return this.scbWrite(address-SCB_BASE,size,value);
    throw new Error(`Peripherique systeme non modele 0x${address.toString(16)}`);
  }
  status(){return {rcuControl:this.clock.get(0),rcuConfig:this.clock.get(4),vtor:this.scb.get(0xd08),
    systickControl:this.systick.get(0x10),nvicEnable:this.nvicEnable.slice(),nvicPending:this.nvicPending.slice(),tickSamples:this.tickSamples};}
}
