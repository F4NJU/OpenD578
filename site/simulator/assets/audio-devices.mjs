/* Electrical audio controls, observed at component boundaries.
 * U2429: UTC QW-R502-031.D pp.4-6. No OEM RAM/PC, no invented speaker net.
 * Codec: TI SLAA557 register map; HPI requests do not prove SCT I2C execution.
 */
const dbGain=db=>10**(db/20);
export class U2429 {
 constructor(){this.channels=[null,null];this.bits=[];this.frames=[];this.accepted=0;this.rejected=0;}
 disconnect(){this.bits=[];} // GPIO input/high-Z does not reset this external IC.
 gpio(before,after,time=null){
  const clk=0x4000,data=0x2000;
  if(!(before&clk)&&(after&clk)){this.bits.push(+(!!(after&data)));if(this.bits.length>11)this.bits.shift();}
  // DATA must remain high at the FALLING CLOCK edge: this is the latch,
  // unlike the ordinary bit-1 waveform which lowers DATA before CLOCK.
  if((before&clk)&&!(after&clk)&&(after&data)){
   const bits=this.bits;this.bits=[];
   if(bits.length!==11||bits[9]!==1||bits[10]!==1){this.rejected++;return;}
   const word=bits.reduce((v,b,i)=>v|(b<<i),0),code=(word>>>2)&127,coarse=code&31,fine=code>>>5;
   if(coarse>21){this.rejected++;return;}
   const mute=coarse===0,attenuationDb=mute?null:4*(21-coarse)+3-fine;
   const state={code,mute,attenuationDb,gain:mute?0:dbGain(-attenuationDb)};
   const targets=bits[1]?[bits[0]]:[0,1]; // D0 channel, D1 individual=1/common=0.
   for(const channel of targets)this.channels[channel]={...state};
   this.accepted++;this.frames.push({sequence:this.accepted,time,word,code,targets:targets.map(i=>i+1),mute,attenuationDb});
   if(this.frames.length>256)this.frames.shift();
  }
 }
 process(channel,samples){
  if(![1,2].includes(channel))throw new RangeError('U2429 channel 1/2');
  const state=this.channels[channel-1];if(!state)throw new Error('U2429 attenuation not yet latched');
  // Nominal small-signal transfer of this component only. No noise, clipping,
  // amplifier, source routing or loudspeaker acoustics are claimed here.
  return Float32Array.from(samples,x=>x*state.gain);
 }
 status(){return {component:'U2429-compatible',DATA:'PA13',CLOCK:'PA14',pinMapping:'OEM GPIO driver; physical continuity unmeasured',channels:this.channels.map((state,i)=>({channel:i+1,known:state!==null,...state})),accepted:this.accepted,rejected:this.rejected,pendingBits:this.bits.length,frames:this.frames,nominalSmallSignalTransfer:true,electricalTimingQualified:false,powerAndLogicLevelTranslationQualified:false,physicalSpeakerNetsQualified:false};}
}

export class Aic3204ControlObserver {
 constructor(){this.page=0;this.registers=new Map();this.commands=0;this.resets=0;}
 write(register,value){
  if(!Number.isInteger(register)||register<0||register>127||!Number.isInteger(value)||value<0||value>255)throw new RangeError('AIC3204 register/value');
  this.commands++;
  if(register===0){this.page=value;return;}
  if(this.page===0&&register===1&&(value&1)){this.registers.clear();this.page=0;this.resets++;return;}
  this.registers.set(`${this.page}:${register}`,value);
 }
 get(page,register){return this.registers.get(`${page}:${register}`)??null;}
 driver(register){
  const raw=this.get(1,register);if(raw===null)return {known:false};
  const code=raw&63,gainDb=code>=58?code-64:code<=29?code:null;
  return {known:true,raw,mute:!!(raw&64),gainDb,reservedCode:gainDb===null,qualification:'gain field only; power, routing and Class-D state require separate commands'};
 }
 mic(register){const raw=this.get(1,register);if(raw===null)return {known:false};const enabled=!(raw&128),code=raw&127;return {known:true,raw,gainEnabled:enabled,gainDb:!enabled?0:code<=95?code/2:null,reservedCode:enabled&&code>95};}
 signedGain(page,register,step,min,max){const raw=this.get(page,register);if(raw===null)return {known:false};const signed=raw<128?raw:raw-256,gainDb=signed*step;return {known:true,raw,gainDb:gainDb>=min&&gainDb<=max?gainDb:null,reservedCode:gainDb<min||gainDb>max};}
 agc(base){const control=this.get(0,base),maximum=this.get(0,base+2),attack=this.get(0,base+3),decay=this.get(0,base+4);return {controlKnown:control!==null,enabled:control===null?null:!!(control&128),targetDbFS:control===null?null:[-5.5,-8,-10,-12,-14,-17,-20,-24][(control>>>4)&7],maximumGainDb:maximum===null?null:Math.min(maximum&127,116)/2,maximumGainRecommended:maximum===null?null:(maximum&127)<=116,attackWordClocks:attack===null?null:(2*(attack>>>3)+1)*32*2**(attack&7),decayWordClocks:decay===null?null:(2*(decay>>>3)+1)*512*2**(decay&7),dynamicResponseEmulated:false};}
 status(){return {component:'TLV320AIC3204',source:'MCU codec register requests over SCT HPI',codecI2cExecutionObserved:false,resetBaselineKnown:false,page:this.page,commands:this.commands,resets:this.resets,registers:Object.fromEntries(this.registers),drivers:{HPL:this.driver(16),HPR:this.driver(17),LOL:this.driver(18),LOR:this.driver(19)},micPGA:{left:this.mic(59),right:this.mic(60)},digitalDAC:{left:this.signedGain(0,65,0.5,-63.5,24),right:this.signedGain(0,66,0.5,-63.5,24)},digitalADC:{left:this.signedGain(0,83,0.5,-12,20),right:this.signedGain(0,84,0.5,-12,20)},AGC:{left:this.agc(86),right:this.agc(94)},routingRaw:{HPL:this.get(1,12),HPR:this.get(1,13),LOL:this.get(1,14),LOR:this.get(1,15),leftMicPositive:this.get(1,52),leftMicNegative:this.get(1,54),rightMicPositive:this.get(1,55),rightMicNegative:this.get(1,57)},PCMTransportQualified:false,correctionCoefficientsQualified:false};}
}

// Sicomm Packet Interface v1.0, section 1.2.74: 0x70, 24 kHz,
// three straight-form second-order IIR sections, signed MSB-first Q16.14.
export class SctAudioControl {
 constructor(){this.filters={RX:[null,null,null],TX:[null,null,null]};this.delay={RX:Array.from({length:3},()=>[0,0,0,0]),TX:Array.from({length:3},()=>[0,0,0,0])};this.iqGains=null;this.modulationGain=null;this.demodulationGain=null;this.analogConfig=null;this.updates=0;}
 field(id,bytes){
  const word=i=>(bytes[i]<<8)|bytes[i+1];
  if(id===44&&bytes.length===2)this.modulationGain={raw:word(0),linearGain:word(0)/2048,format:'Q16.11'};
  if(id===28&&bytes.length===2)this.demodulationGain={raw:word(0),autoCalibration:word(0)===0,linearGain:word(0)===0?null:word(0)/2048,format:'Q16.11'};
  if(id===60&&bytes.length===11){const mode=bytes[0];this.analogConfig={modeRaw:mode,filterBypass:!!(mode&1),basebandCornerHz:mode&2?3000:2550,skipEmphasis:!!(mode&4),IFchannelKHz:mode&8?25:12.5,subaudioWithTone:!!(mode&16),compander:!!(mode&32),DCSHighPass:!!(mode&64),extra3kHzAttenuation:!!(mode&128),TXbeforeLimiter:{raw:word(1),gain:word(1)/2048},TXafterLimiter:{raw:word(3),gain:word(3)/4096},CTCSS:{raw:word(5),gain:word(5)/4096},DCS:{raw:word(7),gain:word(7)/4096},RXvolume:{raw:word(9),gain:word(9)/2048},source:'documented SCT HPI request; actual FM routing requires separate qualification'};}
  if(id===107&&bytes.length===12){const u=i=>(bytes[i]<<8)|bytes[i+1];this.iqGains={IQ_TX:u(0)/2048,IQ_RX:u(2)/2048,subaudioRX:u(4)/2048,calibrationFrequencyRaw:u(6),DCconfigurationRaw:bytes[8]};}
  if(id!==112)return;
  if(bytes.length!==11)throw new RangeError('SCT EQ payload');
  const select=bytes[0],slot=(select&15)-1,direction=select&32?'TX':'RX';
  if(slot<0||slot>2||(select&192))throw new Error('SCT EQ selection outside documented fields');
  const signed=i=>{const u=(bytes[i]<<8)|bytes[i+1];return (u<32768?u:u-65536)/16384;};
  this.filters[direction][slot]={slot:slot+1,enabled:!!(select&16),a1:signed(1),a2:signed(3),b0:signed(5),b1:signed(7),b2:signed(9),raw:[...bytes]};
  this.delay[direction][slot]=[0,0,0,0];this.updates++;
 }
 processCorrection(direction,samples,sampleRate=24000){
  if(!['RX','TX'].includes(direction)||sampleRate!==24000)throw new RangeError('SCT EQ: RX/TX, 24000 Hz required');
  if(this.filters[direction].some(f=>f===null))throw new Error('SCT EQ configuration incomplete');
  // Nominal transfer function at the documented component boundary, not a
  // substitute PCM route. Actual SCT accumulator width, saturation and filter
  // state transitions have not been captured: this is not bit-exact DSP.
  const out=Float32Array.from(samples);
  for(let i=0;i<3;i++){
   const f=this.filters[direction][i];if(!f.enabled)continue;
   let [x1,x2,y1,y2]=this.delay[direction][i];
   for(let n=0;n<out.length;n++){const x=out[n],y=f.b0*x+f.b1*x1+f.b2*x2-f.a1*y1-f.a2*y2;out[n]=y;x2=x1;x1=x;y2=y1;y1=y;}
   this.delay[direction][i]=[x1,x2,y1,y2];
  }
  return out;
 }
 status(){return {source:'MCU-to-SCT HPI control fields',sampleRate:24000,coefficientFormat:'signed Q16.14, MSB first',filters:this.filters,IQgains:this.iqGains,modulationGain:this.modulationGain,demodulationGain:this.demodulationGain,analogConfig:this.analogConfig,updates:this.updates,nominalCorrectionTransfer:true,bitExactDSP:false,PCMRouteConnected:false,filterUpdateTransientQualified:false};}
}

export function audioStatusText(audio){
 const volume=audio?.attenuator,codec=audio?.codecControl;
 const attenuation=c=>!c.known?'non reçu':c.mute?'coupé':c.attenuationDb===0?'0 dB':`−${c.attenuationDb} dB`;
 const gain=c=>!c?.known?'non reçu':c.gainDb===null?'code réservé':`${c.gainDb>=0?'+':''}${c.gainDb} dB${c.mute?' · coupé':''}`;
 const lines=['U2429 · commandes GPIO PA13 DATA / PA14 CLOCK'];
 if(audio?.QA)for(const b of audio.QA.banks)lines.push(`QA banque ${b.bank} · sélecteur micro brut ${b.microphoneSelectorRaw??'?'} · code micro appliqué ${b.microphoneAppliedCodeRaw??'?'} · gain en dB non qualifié`);
 for(const c of volume?.channels??[])lines.push(`Canal ${c.channel} : ${attenuation(c)}`);
 if(volume)lines.push(`${volume.accepted} trames validées · ${volume.rejected} trames rejetées`);
 lines.push('AIC3204 · demandes du firmware via SCT, I²C interne non observé');
 for(const [name,c]of Object.entries(codec?.drivers??{}))lines.push(`${name} : ${gain(c)}`);
 if(codec){lines.push(`PGA micro G / D : ${gain(codec.micPGA.left)} / ${gain(codec.micPGA.right)}`);lines.push(`DAC numérique G / D : ${gain(codec.digitalDAC.left)} / ${gain(codec.digitalDAC.right)}`);lines.push(`ADC numérique G / D : ${gain(codec.digitalADC.left)} / ${gain(codec.digitalADC.right)}`);const a=codec.AGC?.left;lines.push(`AGC gauche : ${a?.enabled===null||!a?'non reçu':a.enabled?'activé':'désactivé'} · cible ${a?.targetDbFS??'?'} dBFS · gain max. ${a?.maximumGainDb??'?'} dB`);}
 if(audio?.SCTcorrections)for(const direction of ['RX','TX']){const filters=audio.SCTcorrections.filters[direction];lines.push(`Égalisation ${direction} à 24 kHz : ${filters.filter(f=>f!==null).length}/3 configurations reçues · ${filters.filter(f=>f?.enabled).length} activées`);}
 lines.push('Flux audio non raccordé. Liaisons vers HP poste, HP micro et prises externes A/B à qualifier.');
 return lines.join('\n');
}
