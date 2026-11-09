/* D578 wired microphone UART protocol model; no OEM PC/RAM hooks.
 * The microphone MCU firmware is unavailable and is not executed.
 * GPL-3.0-or-later. */
export const MIC_CODES=Object.freeze({'0':1,'1':2,'2':3,'3':4,'4':5,'5':6,'6':7,'7':8,'8':9,'9':10,'*':11,'#':12,'SUB A/B':13,'UP':16,'DOWN':17,'A':26,'B':27,'C':28,'D':29});
const HZ=120000000,BYTE_UNITS=HZ*10/115200;
const normalize=name=>String(name).toUpperCase().replace('SUB_AB','SUB A/B');
export function encodeMicKey({name=null,ptt=false,active=false,longPress=false,lastCode=0}={}){
 const code=name===null?lastCode:MIC_CODES[normalize(name)];if(!Number.isInteger(code)||code<0||code>255)throw new RangeError(`Touche microphone inconnue : ${name}`);
 return Uint8Array.of(0x41,Number(!!ptt),Number(!!active),Number(!!longPress),code,0,0,0x06);
}
export class WiredMicReceiver{
 constructor({onFrame=null}={}){this.onFrame=onFrame;this.rx=[];this.last=null;this.latest=null;this.frames=0;this.rejected=0;this.outOfProfile=0;this.singleAA=0;this.unknownBytes=0;this.history=[];this.error=null;}
 inputByte(byte){
  if(!Number.isInteger(byte)||byte<0||byte>255)throw new RangeError('Octet UART attendu');
  if(!this.rx.length){if(byte===0x53)this.rx.push(byte);else if(byte===0xaa)this.singleAA++;else{this.unknownBytes++;this.error='Octet hors trame';this.latest=null;}return;}
  this.rx.push(byte);if(this.rx.length<16)return;const raw=this.rx;this.rx=[];
  if(raw[15]!==6){this.rejected++;this.latest=null;this.error='Fin de trame incorrecte';const start=raw.indexOf(0x53,1);if(start>=0)this.rx=raw.slice(start);this.record({raw,accepted:false});return;}
  this.frames++;const supported=raw.slice(1,8).every(v=>v===0||v===1)&&raw[9]===16;
  const frame={raw,profileSupported:supported,rxA:raw[1],gateA:raw[2],txA:raw[3],rxB:raw[4],gateB:raw[5],txB:raw[6],main:raw[7]===0?'A':raw[7]===1?'B':null,unknown:Object.fromEntries([8,9,10,11,12,13,14].map(i=>[i,raw[i]]))};
  this.last=frame;this.latest=supported?frame:null;this.error=supported?null:'Trame hors profil V1.21';if(!supported)this.outOfProfile++;this.record({...frame,accepted:true});this.onFrame?.(frame);
 }
 record(frame){this.history.push(frame);if(this.history.length>32)this.history.shift();}
 inputBytes(bytes){for(const b of bytes)this.inputByte(b);}
 invalidate(){this.latest=null;this.rx=[];this.error='Microphone déconnecté';}
 status(){const f=!this.rx.length&&!this.error?this.latest:null;const lamp=(rx,tx)=>({green:!!rx,red:!!tx});return{received:!!this.last,frames:this.frames,rejected:this.rejected,outOfProfile:this.outOfProfile,singleAA:this.singleAA,unknownBytes:this.unknownBytes,pendingBytes:this.rx.length,error:this.error,raw:this.last?.raw??null,...(f??{}),main:f?.main??null,commandsValid:!!f,indicators:f?{A:lamp(f.rxA,f.txA),B:lamp(f.rxB,f.txB),mainA:f.main==='A',mainB:f.main==='B'}:null,lastFrame:this.last,history:this.history.slice(),physicalLEDMappingQualified:false};}
}
export class WiredMicrophoneCable{
 constructor({rxByteFromWire}){if(typeof rxByteFromWire!=='function')throw new TypeError('Connexion UART MCU requise');this.rxByteFromWire=rxByteFromWire;this.display=new WiredMicReceiver();this.connected=true;this.locked=false;this.key=null;this.ptt=false;this.lastCode=0;this.longSent=false;this.releaseAt=Infinity;this.longAt=Infinity;this.minimumUntil=0;this.longMs=800;this.packets=[];this.sentFrames=0;this.sentBytes=0;this.inputHistory=[];this.time=0;this.keepaliveMs=1000;this.keepaliveAt=HZ;this.keepalives=0;this.ackRequired=true;this.awaitingAck=false;}
 // Low-level wire helper, independent from the timed UI input state machine.
 press(options={}){const raw=encodeMicKey(options);if(!this.connected)throw Error('Microphone déconnecté');for(const b of raw)this.rxByteFromWire(b);return raw;}
 emit(at){const raw=encodeMicKey({name:this.key,ptt:this.ptt,active:this.key!==null,longPress:this.key!==null&&this.longSent,lastCode:this.lastCode});this.packets.push({at,raw});this.inputHistory.push({at,raw:Array.from(raw)});if(this.inputHistory.length>64)this.inputHistory.shift();return raw;}
 input(options={},now=this.time){
  if(!this.connected)throw Error('Microphone déconnecté');const minimumMs=options.minimumMs??200;if(!Number.isFinite(minimumMs)||minimumMs<20||minimumMs>10000)throw Error('Appui micro : 20 à 10000 ms');
  const name=options.name==null?null:normalize(options.name);if(name!==null&&!(name in MIC_CODES))throw Error('Touche microphone inconnue');if(name!==null&&options.active&&this.key!==null&&this.key!==name)throw Error('Une seule touche du clavier micro à la fois');if(name!==null&&this.locked&&['UP','DOWN'].includes(name))return null;
  this.time=now;let changed=false;if(options.ptt!==undefined&&this.ptt!==!!options.ptt){this.ptt=!!options.ptt;changed=true;}
  if(name!==null&&options.active){if(this.key!==name){this.key=name;this.lastCode=MIC_CODES[name];this.longSent=false;this.minimumUntil=now+minimumMs*HZ/1000;this.longAt=now+this.longMs*HZ/1000;changed=true;}this.releaseAt=Infinity;}
  else if(name!==null&&this.key===name){if(now<this.minimumUntil)this.releaseAt=this.minimumUntil;else{this.key=null;this.longAt=this.releaseAt=Infinity;this.longSent=false;changed=true;}}
  if(options.longPress&&this.key!==null&&!this.longSent){this.longSent=true;this.longAt=Infinity;changed=true;}return changed?this.emit(now):null;
 }
 configure({connected=this.connected,locked=this.locked,longMs=this.longMs,keepaliveMs=this.keepaliveMs,ackRequired=this.ackRequired}={},now=this.time){
  if(typeof ackRequired!=='boolean'||typeof connected!=='boolean'||typeof locked!=='boolean'||!Number.isFinite(longMs)||longMs<200||longMs>10000||!Number.isFinite(keepaliveMs)||keepaliveMs!==0&&(keepaliveMs<100||keepaliveMs>10000))throw Error('Configuration microphone invalide');this.time=now;const reconnect=connected&&!this.connected;this.connected=connected;this.longMs=longMs;if(reconnect||keepaliveMs!==this.keepaliveMs)this.keepaliveAt=keepaliveMs?now+keepaliveMs*HZ/1000:Infinity;this.keepaliveMs=keepaliveMs;this.ackRequired=ackRequired;if(!ackRequired)this.awaitingAck=false;
  if(!connected){this.key=null;this.ptt=false;this.longSent=false;this.releaseAt=this.longAt=Infinity;this.packets=[];this.awaitingAck=false;this.display.invalidate();}
  if(locked&&!this.locked&&['UP','DOWN'].includes(this.key)){this.key=null;this.longSent=false;this.releaseAt=this.longAt=Infinity;if(connected)this.emit(now);}this.locked=locked;
  if(reconnect){this.display=new WiredMicReceiver();this.emit(now);}return this.status();
 }
 releaseAll(now=this.time){if(!this.connected)return null;this.time=now;const was=this.key!==null||this.ptt;this.key=null;this.ptt=false;this.longSent=false;this.releaseAt=this.longAt=Infinity;return was?this.emit(now):null;}
 nextInput(){return this.connected?Math.min(this.releaseAt,this.longAt,(this.awaitingAck?Infinity:this.packets[0]?.at??Infinity)):Infinity;}
 next(){return this.connected?Math.min(this.nextInput(),this.keepaliveMs&&!this.awaitingAck?this.keepaliveAt:Infinity):Infinity;}
 advance(now,uart){
  this.time=now;if(!this.connected)return;
  // A requested short release takes precedence over a later long-press event.
  if(now>=this.releaseAt){const at=this.releaseAt;this.key=null;this.longSent=false;this.releaseAt=this.longAt=Infinity;this.emit(at);}
  if(this.key!==null&&now>=this.longAt){const at=this.longAt;this.longSent=true;this.longAt=Infinity;this.emit(at);}
  while(!this.awaitingAck&&this.packets.length&&this.packets[0].at<=now){const p=this.packets.shift();uart.schedule(p.raw,{at:Math.max(p.at,now),byteSteps:BYTE_UNITS});this.sentFrames++;this.sentBytes+=p.raw.length;this.awaitingAck=this.ackRequired;}
  // Autonomous presence byte from the published D578 software-mic profile.
  // No response to AA/status packets is invented. Period is not a measured MCU timing.
  if(this.keepaliveMs&&!this.awaitingAck)while(now>=this.keepaliveAt){uart.schedule([6],{at:this.keepaliveAt,byteSteps:BYTE_UNITS});this.keepaliveAt+=this.keepaliveMs*HZ/1000;this.keepalives++;this.sentBytes++;}
 }
 fromRadioTxByte(byte){if(this.connected){const singleAA=byte===170&&!this.display.rx.length;this.display.inputByte(byte);if(singleAA)this.awaitingAck=false;}}
 status(){return{...this.display.status(),connected:this.connected,locked:this.locked,heldKey:this.key,ptt:this.ptt,longPress:this.longSent,longThresholdMs:this.longMs,longThresholdMeasured:false,sourceBaud:115200,sentFrames:this.sentFrames,sentBytes:this.sentBytes,queuedFrames:this.packets.length,inputHistory:this.inputHistory.slice(),audioSamplesRouted:false,microphoneMCUExecuted:false,ackRequired:this.ackRequired,awaitingAck:this.awaitingAck,keepaliveMs:this.keepaliveMs,keepalives:this.keepalives,keepaliveTimingMeasured:false,generatedResponses:0};}
}
