import {AudioVolumeStream} from './audio-volume-stream.mjs?build=web0160r1';
import {AudioPcmInput} from './audio-pcm-input.mjs?build=web0160r1';
/* Hardware-only I/O model for D578UV PRO GD32. No OEM SRAM variable access.
 * Based on OpenD578 V11.8 mapping; unknown circuits are NOT inferred.
 * Copyright (c) 2026 OpenD578 contributors; GPL-3.0-or-later.
 */
import { WiredMicrophoneCable } from './wired-microphone.mjs?build=web0160r1';
import { NandSpi } from './nand-spi.mjs?build=web0160r1';
import { U2429 } from './audio-devices.mjs?build=web0160r1';
export const GPIO_BASE = Object.freeze({A:0x40010800,B:0x40010c00,C:0x40011000,D:0x40011400,E:0x40011800,F:0x40011c00,G:0x40012000});
export const ADC0=0x40012400, USART0=0x40013800, USART1=0x40004400;
export const AFIO=0x40010000,EXTI=0x40010400;
const INPUT_KEYS=Object.freeze({POWER:['A',0],DIAL_PRESS:['A',1]});
const ANALOG_KEYS=Object.freeze({P1:[8,250],P2:[8,1000],P3:[8,2000],MENU:[8,3000],P4:[9,250],P5:[9,1000],P6:[9,2000],EXIT:[9,3000]});
const PIN_HIGH=0xffff;
function uint32(v) { return v>>>0; }
function le(bytes){return bytes.reduce((n,b,i)=>n|(b<<(8*i)),0)>>>0;}
export class Lcd8080 {
  constructor(){this.reset();}
  reset(){this.width=128;this.height=160;this.pixels=new Uint16Array(128*160);this.displayOn=false;this.sleep=true;this.command=null;this.params=[];this.rangeX=[0,127];this.rangeY=[0,159];this.cursorX=0;this.cursorY=0;this.highByte=null;this.format=0x55;this.orientation=0;this.writes=0;}
  input(byte, isData){
    byte&=255;
    if(!isData){this.command=byte;this.params=[];this.highByte=null;
      if(byte===0x01)this.reset();
      if(byte===0x10)this.sleep=true;
      if(byte===0x11)this.sleep=false;
      if(byte===0x28)this.displayOn=false;
      if(byte===0x29)this.displayOn=true;
      if(byte===0x2c){this.cursorX=this.rangeX[0];this.cursorY=this.rangeY[0];}
      return;
    }
    switch(this.command){
      case 0x2a:case 0x2b:{
        this.params.push(byte);if(this.params.length===4){const a=(this.params[0]<<8)|this.params[1];const b=(this.params[2]<<8)|this.params[3];
          if(this.command===0x2a)this.rangeX=[a,b];else this.rangeY=[a,b];this.params=[];}
        break;
      }
      case 0x36:this.orientation=byte;break;
      case 0x3a:this.format=byte;break;
      case 0x2c:{
        if(this.highByte===null){this.highByte=byte;break;}
        const pixel=(this.highByte<<8)|byte;this.highByte=null;
        if(this.cursorX<this.width&&this.cursorY<this.height)this.pixels[this.cursorY*this.width+this.cursorX]=pixel;
        this.writes++;this.cursorX++;
        if(this.cursorX>this.rangeX[1]){this.cursorX=this.rangeX[0];this.cursorY++;if(this.cursorY>this.rangeY[1])this.cursorY=this.rangeY[0];}
        break;
      }
    }
  }
  // Raw pixels are intentionally returned without an invented OEM framebuffer.
  snapshot(){return {width:this.width,height:this.height,pixels:this.pixels.slice(),displayOn:this.displayOn,sleep:this.sleep,writes:this.writes,orientation:this.orientation,format:this.format};}
}
export class BoardIO {
  constructor({onChange=null,nandStorage=null}={}) {
    this.onChange=onChange;this.audioInput=new AudioPcmInput();
    this.nand=nandStorage?new NandSpi(nandStorage):null;
    this.mic=new WiredMicrophoneCable({rxByteFromWire:b=>this.uartRx.push(b)});
    this.reset();
  }
  reset({preserveInputs=false,preserveExternal=false}={}){
    if(!preserveExternal)this.audioInput.clear();
    const external=preserveInputs&&this.input?{input:{...this.input},keys:new Set(this.keys),adc:new Map(this.adc)}:null;
    this.out=Object.fromEntries(Object.keys(GPIO_BASE).map(k=>[k,0]));
    if(!preserveExternal)this.nand?.reset();
    this.input=Object.fromEntries(Object.keys(GPIO_BASE).map(k=>[k,PIN_HIGH]));
    this.config={};this.regs=new Map();this.keys=new Set();
    for(const base of Object.values(GPIO_BASE)){
      this.regs.set(base,0x44444444);this.regs.set(base+4,0x44444444);
      this.regs.set(base+0x0c,0);
    }
    for(const o of [0,4,8,0x0c,0x10,0x14,0x1c])this.regs.set(AFIO+o,0);
    for(const o of [0,4,8,0x0c,0x10,0x14,0x18])this.regs.set(EXTI+o,0);
    for(const o of [0,4,8,0x0c,0x10,0x14,0x18,0x1c,0x20,0x24,0x28,0x2c,0x30,0x34,0x38,0x3c,0x40,0x44,0x48])this.regs.set(ADC0+o,0);
    this.adc=new Map([[6,262],[8,4095],[9,4095],[10,1034],[11,2600],[12,1800],[15,1800]]);
    this.adcChannel=8;this.uartRx=[];this.uartTxCount=0;this.usartEnabled=false;
    this.gpsRx=[];this.gpsTx=[];this.gpsMode='absent';this.gpsFrames=0;
    for(const base of [USART0,USART1]){
      this.regs.set(base,0xc0);this.regs.set(base+8,0);
      this.regs.set(base+0x0c,0);this.regs.set(base+0x10,0);this.regs.set(base+0x14,0);
    }
    if(!preserveExternal||!this.lcd)this.lcd=new Lcd8080();
    if(!preserveExternal||!this.volumeChip)this.volumeChip=new U2429();
    else this.volumeChip.disconnect();
    if(!preserveExternal||!this.volumePcm)this.volumePcm=new AudioVolumeStream(this.volumeChip);
    this.volumeChip.onBeforeLatch=time=>this.volumePcm.beforeLatch(time);
    this.ledRaw=null;this.ledBits=[];this.green=false;this.red=false;
    this.lightBits=[];this.lightRaw=new Map();this.lcdBacklight=0;this.lcdBacklightKnown=false;
    this.lastReset=0;
    this.input.A=(this.input.A|3)>>>0;
    if(external){this.input=external.input;this.keys=external.keys;this.adc=external.adc;}
  }
  setKey(name,down){
    name=String(name).toUpperCase();down=!!down;
    if(name in INPUT_KEYS){const [port,bit]=INPUT_KEYS[name];this.driveInputs(port,down?this.input[port]&~(1<<bit):this.input[port]|(1<<bit));if(down)this.keys.add(name);else this.keys.delete(name);}
    else if(name in ANALOG_KEYS){
      const nextKeys=new Set(this.keys);if(down)nextKeys.add(name);else nextKeys.delete(name);
      const [channel]=ANALOG_KEYS[name];const held=[...nextKeys].filter(k=>ANALOG_KEYS[k]?.[0]===channel);
      if(held.length>1)throw new Error(`Touches simultanees sur reseau ADC ${channel} non qualifiees`);
      this.keys=nextKeys;this.adc.set(channel,held.length?ANALOG_KEYS[held[0]][1]:4095);
    }else throw new Error(`Touche inconnue: ${name}`);
  }
  setVolume(which,adc12){const chan=which==='A'?12:which==='B'?15:null;if(!chan)throw new Error('Volume A/B');if(!Number.isInteger(adc12)||adc12<0||adc12>4095)throw new RangeError('ADC 12 bits');this.adc.set(chan,adc12);}
  driveInputs(port,value){const before=this.input[port],changed=(before^value)&0xffff;this.input[port]=value&0xffff;
    for(let line=0;line<16;line++){const bit=1<<line,mode=this.mode(port,line);if(!(changed&bit)||!mode||(mode&3))continue;const mapping=this.regs.get(AFIO+8+(line>>2)*4),selected=(mapping>>>((line&3)*4))&15;if(selected!==port.charCodeAt(0)-65)continue;const trigger=this.regs.get(EXTI+(value&bit?8:12));if(!(trigger&bit))continue;this.regs.set(EXTI+20,this.regs.get(EXTI+20)|bit);if(this.regs.get(EXTI)&bit)this.hardware?.pend(line<5?6+line:line<10?23:40);}
  }
  releaseEncoder(){this.driveInputs('C',this.input.C|0x300);}
  rotate(direction){ // One PC8 transition along a valid quadrature sequence, not an inferred physical detent.
    if(!['up','down'].includes(direction))throw new Error('Direction up/down');
    const h=this.hardware,phase=300000; // 2.5 ms of bench time between A/B transitions.
    if(!h){const first=direction==='up'?0x200:0x100,second=first^0x300;this.driveInputs('C',this.input.C^first);this.driveInputs('C',this.input.C^second);return;}
    const q=h.encoderEvents,initial=q.length?h.encoderTail:this.input.C&0x300,final=initial^0x300,first=direction==='up'?0x200:0x100,second=first^0x300,start=Math.max(h.m.time,q.length?q.at(-1).at+phase:h.m.time);
    q.push({at:start,bit:first,high:!!(final&first)},{at:start+phase,bit:second,high:!!(final&second)});h.encoderTail=final;
    this.onChange?.({kind:'encoder-quadrature-step',direction,initial,final,phaseVirtualUnits:phase,physicalDetentMappingQualified:false});
  }
  micPress(key){return this.mic.press(key);}
  // The MCU samples physical input levels, not the GPIO output latch.
  mode(p,n){return ((this.regs.get(GPIO_BASE[p]+(n<8?0:4))??0x44444444)>>>((n&7)*4))&15;}
  physicalLevels(p,sampleSct=false) {
    let input=this.input[p];
    if(this.nand && p==='A')input=(input&~(1<<15))|(this.nand.miso<<15);
    if(this.nand && p==='B')input=(input&~(1<<14))|(this.nand.io0<<14);
    if(this.hardware){const h=this.hardware;
      if(p==='B'){input=(input&~64)|(h.fm.input()<<6);if(h.rf.bank!==null&&h.rf.miso!==null)input=(input&~16)|(h.rf.miso<<4);}
      if(p==='D'){input=(input&~32)|(h.sct.rx.length?0:32);if(sampleSct&&h.sct.expected&&this.regs.get(GPIO_BASE.D+4)===0x88888888&&!(this.out.D&20))input=(input&255)|h.sct.input(this.out.D);}
    }
    const base=GPIO_BASE[p];let levels=0;
    for(let bit=0;bit<16;bit++){
      const mode=((this.regs.get(base+(bit<8?0:4))??0x44444444)>>>((bit&7)*4))&0xf;
      const isOutput=(mode&3)!==0;
      if((isOutput?this.out[p]:input)&(1<<bit))levels|=1<<bit;
    }
    return levels>>>0;
  }
  _readReg(a){
    if(!this.regs.has(a))throw new Error(`Registre materiel inconnu 0x${a.toString(16)}`);
    return this.regs.get(a);
  }
  injectGpsNmea(sentence) {
    if(typeof sentence!=='string'||sentence.length>160)throw new Error('Trame NMEA incorrecte');
    let frame=sentence.replace(/[\r\n]+$/,'');
    const star=frame.indexOf('*'),body=frame.slice(1,star>=0?star:undefined);
    if(!frame.startsWith('$')||!body||!/^[\x20-\x7e]+$/.test(body)||/[$*]/.test(body)||star>=0&&!/^\*[0-9a-fA-F]{2}$/.test(frame.slice(star)))throw new Error('Trame NMEA incorrecte');
    let checksum=0;for(const char of body)checksum^=char.charCodeAt(0);
    const given=checksum.toString(16).toUpperCase().padStart(2,'0');
    // Preserve an explicitly supplied checksum, including a bad one used as a wire fault.
    if(star<0)frame+='*'+given;
    for(const byte of new TextEncoder().encode(frame+'\r\n'))this.gpsRx.push(byte);
    this.gpsFrames++;
  }
  read(address,size=4){
    if(address>=EXTI&&address<EXTI+0x20)return this._readReg(address);
    if(address>=AFIO&&address<AFIO+0x20)return this._readReg(address);
    for(const [p,base] of Object.entries(GPIO_BASE))if(address>=base&&address<base+0x20){const off=address-base;
      if(off===0x08)return this.physicalLevels(p,true);
      if(off===0x0c)return this.out[p]>>>0;
      return this._readReg(address);
    }
    if(address===ADC0+0x4c)return this.adc.get(this.adcChannel)??4095;
    if(address>=ADC0&&address<ADC0+0x50)return this._readReg(address);
    for(const [base,rx] of [[USART0,this.uartRx],[USART1,this.gpsRx]]){
      if(address===base)return uint32((this._readReg(base)&~0x20)|(rx.length?0x20:0));
      if(address===base+4){
        if(!rx.length)throw new Error(`USART${base===USART0?0:1}: DR lu sans octet recu`);
        return rx.shift();
      }
      if(address>=base&&address<=base+0x14)return this._readReg(address);
    }
    return this._readReg(address);
  }
  write(address,value,size=4){
    value=uint32(value);
    if(address>=EXTI&&address<EXTI+0x20){
      if(!this.regs.has(address))throw new Error(`EXTI non modele: 0x${address.toString(16)}`);
      if(address===EXTI+0x14)this.regs.set(address,this._readReg(address)&~value);
      else if(address===EXTI+0x10){this.regs.set(EXTI+20,this.regs.get(EXTI+20)|value);this.regs.set(address,value);}
      else this.regs.set(address,value);
      return;
    }
    if(address>=AFIO&&address<AFIO+0x20){
      if(!this.regs.has(address))throw new Error(`AFIO non modele: 0x${address.toString(16)}`);
      this.regs.set(address,value);if(address===AFIO+4&&!this.volumeGpioReady())this.volumeChip.disconnect();return;
    }
    if(address>=ADC0&&address<ADC0+0x50 && !this.regs.has(address) && address!==ADC0+0x4c){
      throw new Error(`ADC0 registre non modele: 0x${address.toString(16)}`);
    }
    if(address===USART0+4){
      if((this._readReg(USART0+0x0c)&0x2008)!==0x2008||!this._readReg(USART0+8))throw new Error('USART0: emission avant activation UART/TX/baud');
      this.uartTxCount++;this.mic.fromRadioTxByte(value&255);this.onChange?.({kind:'usart-tx',byte:value&255});return;
    }
    if(address===USART1+4){
      if((this._readReg(USART1+0x0c)&0x2008)!==0x2008||!this._readReg(USART1+8))throw new Error('USART1: emission avant activation UART/TX/baud');
      this.gpsTx.push(value&255);return;
    }
    if(!(address>=GPIO_BASE.A&&address<GPIO_BASE.G+0x20)
        &&!(address>=USART0&&address<=USART0+0x14)
        &&!(address>=USART1&&address<=USART1+0x14)
        &&!(address>=ADC0&&address<=ADC0+0x4c)){
      throw new Error(`Peripherique non modele 0x${address.toString(16)}`);
    }
    for(const [p,base] of Object.entries(GPIO_BASE))if(address>=base&&address<base+0x20){
      const off=address-base;const before=this.out[p];const pinsBefore=this.physicalLevels(p);
      const h=this.hardware,ports=['B','C','E'];const rfBefore=h?Object.fromEntries(ports.map(p=>[p,this.physicalLevels(p)])):null;
      const oldMode=this.mode(p,6),oldD=this.out.D;this.regs.set(address,value);
      if(off===0x0c)this.out[p]=value&0xffff;
      if(off===0x10)this.out[p]=((before|(value&0xffff))&~((value>>>16)&0xffff))&0xffff;
      if(off===0x14)this.out[p]=(before&~(value&0xffff))&0xffff;
      // Input reads see the output level when configured as output. Exact direction comes from CTL0/CTL1.
      if([0x0c,0x10,0x14].includes(off)){
        this.regs.set(base+0x0c,this.out[p]);
        if(p==='B' && this.nand){
          const mask=off===0x0c?0xffff:off===0x10?((value&0xffff)|((value>>>16)&0xffff)):(value&0xffff);
          this.nand.drive(this.out.B,mask);
        }
        this._outputsChanged(p,pinsBefore,this.physicalLevels(p));
      }
      if(p==='A'&&[0,4].includes(off)){
        if(this.volumeGpioReady())this.volumeChip.gpio(pinsBefore,this.physicalLevels('A'),h?.m.time??null);
        else this.volumeChip.disconnect();
      }
      if(h){
        if(p==='B')h.fm.gpio(before,this.out.B,oldMode,this.mode('B',6));
        if(p==='D'&&[12,16,20].includes(off))h.sct.gpio(oldD,this.out.D,this.regs.get(GPIO_BASE.D+4));
        if(this.mode('B',3)&3)h.rf.armed=true;
        if(ports.includes(p)&&[0,4,12,16,20].includes(off))h.rf.gpio(rfBefore,Object.fromEntries(ports.map(p=>[p,this.physicalLevels(p)])),this.mode('B',4),h.m.time);
      }
      return;
    }
    this.regs.set(address,value);
    if(address===ADC0+0x34){this.adcChannel=value&31;return;}
    if(address===ADC0+0x38){this.adcChannel=value&31;return;}
  }
  volumeGpioReady(){return ((this.regs.get(AFIO+4)>>>24)&7)===4&&[13,14].every(n=>{const mode=this.mode('A',n);return (mode&3)&&!(mode&8);});}
  _outputsChanged(p,before,after){
    const rising=b=>!(before&(1<<b))&&!!(after&(1<<b));
    const falling=b=>!!(before&(1<<b))&&!(after&(1<<b));
    if(p==='A'&&this.volumeGpioReady())this.volumeChip.gpio(before,after,this.hardware?.m.time??null);
    if(p==='B'&&(this.mode('B',12)&3)&&falling(12))this.lcd.reset();
    const lcdReady=[10,11,13].every(n=>this.mode('B',n)&3)&&Array.from({length:8},(_,i)=>i+7).every(n=>this.mode('E',n)&3);
    if(lcdReady&&p==='B'&&rising(10)&&!(after&(1<<13))){const data=(this.physicalLevels('E')>>>7)&255;const isData=!!(after&(1<<11));this.lcd.input(data,isData);this.onChange?.({kind:'lcd-byte'});}
    if(p==='E'&&rising(4)){
      this.ledBits.push((after>>>3)&1);
      if(this.ledBits.length===8){this.ledRaw=this.ledBits.reduce((v,b,i)=>v|(b<<i),0);this.ledBits=[];
        this.green=!!(this.ledRaw&0x08);this.red=!!(this.ledRaw&0x10);this.onChange?.({kind:'led',raw:this.ledRaw});}
    }
    const lightingReady=(this.mode('A',5)&3)&&(this.mode('B',3)&3)&&(this.mode('B',4)&3);
    if(lightingReady&&p==='A'&&falling(5))this.lightBits=[];
    if(lightingReady&&p==='B'&&rising(3)&&!(this.out.A&(1<<5)))this.lightBits.push((after>>>4)&1);
    if(lightingReady&&p==='A'&&rising(5)&&this.lightBits.length===12){
      const word=this.lightBits.reduce((v,b)=>(v<<1)|b,0);const address=word>>>8,level=word&255;
      this.lightRaw.set(address,level);
      if(address===8){this.lcdBacklight=level;this.lcdBacklightKnown=true;}
      this.onChange?.({kind:'backlight',address,value:level});
    }
  }
  status(){return {volumeChip:this.volumeChip.status(),nandSpi:this.nand?.summary()??null,gps:{mode:this.gpsMode,queued:this.gpsRx.length,sent:this.gpsTx.length,frames:this.gpsFrames},buttons:[...this.keys],adc:Object.fromEntries(this.adc),green:this.green,red:this.red,ledRaw:this.ledRaw,backlightRaw:this.lcdBacklight,backlightKnown:this.lcdBacklightKnown,lighting:Object.fromEntries(this.lightRaw),lcd:{displayOn:this.lcd.displayOn,sleep:this.lcd.sleep,writes:this.lcd.writes},mic:this.mic.status(),usartTx:this.uartTxCount,usartRxQueued:this.uartRx.length};}
}
