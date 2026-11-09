/* External PC0/ADC10 stimulus. No guest RAM, no assumed FM codec/speaker route.
 * Uses the bench's 120M virtual instruction units/s, not physical ADC cycles. */
export class AudioPcmInput {
 constructor(){this.clear();}
 clear(){this.config=null;this.converted=0;this.observed=[];}
 configure({codes,sampleRate,idleCode=2048},now){
  if(!codes||!Number.isInteger(codes.length)||!codes.length||codes.length>2304000||!Number.isInteger(sampleRate)||sampleRate<8000||sampleRate>192000||!Number.isInteger(idleCode)||idleCode<0||idleCode>4095||!Number.isSafeInteger(now)||now<0)throw Error('Audio ADC : codes 12 bits, 8–192 kHz, taille limitée');
  if(codes.length>12*sampleRate)throw Error('Audio ADC : durée maximum 12 secondes');
  const next=Uint16Array.from(codes);for(let i=0;i<codes.length;i++)if(!Number.isInteger(codes[i])||codes[i]<0||codes[i]>4095)throw Error('Audio ADC : code hors 0..4095');
  this.config={codes:next,sampleRate,idleCode,start:now};this.converted=0;this.observed=[];
 }
 valueAt(now){const c=this.config;if(!c)return null;const i=Math.floor((now-c.start)*c.sampleRate/120000000);return i<0||i>=c.codes.length?c.idleCode:c.codes[i];}
 conversion(now,value){if(!this.config)return;this.converted++;if(this.observed.length<8192)this.observed.push({time:now,value});}
 status(){const c=this.config;return {connected:!!c,pin:'PC0',ADCchannel:10,sampleRate:c?.sampleRate??null,length:c?.codes.length??0,start:c?.start??null,idleCode:c?.idleCode??null,converted:this.converted,captured:this.observed.length,captureTruncated:this.converted>this.observed.length,source:'external 12-bit ADC stimulus',timing:'120M virtual units/s; ADC model 64 units/conversion; not cycle accurate',FMvoiceRouteQualified:false};}
}
// Strict PCM16 WAV import. Codes are an explicit stimulus mapping, not volts.
export function wavToAdcCodes(buffer,{bias=2048,amplitude=1024}={}){
 const v=new DataView(buffer),txt=(o,n)=>String.fromCharCode(...new Uint8Array(buffer,o,n));
 if(buffer.byteLength<44||txt(0,4)!=='RIFF'||txt(8,4)!=='WAVE'||v.getUint32(4,true)+8!==buffer.byteLength)throw Error('WAV RIFF invalide');
 let format=null,data=null;
 for(let o=12;o+8<=buffer.byteLength;){const n=v.getUint32(o+4,true),end=o+8+n;if(end>buffer.byteLength)throw Error('WAV tronqué');const id=txt(o,4);
  if(id==='fmt '){if(format||n<16)throw Error('Format WAV invalide');format={type:v.getUint16(o+8,true),channels:v.getUint16(o+10,true),sampleRate:v.getUint32(o+12,true),byteRate:v.getUint32(o+16,true),align:v.getUint16(o+20,true),bits:v.getUint16(o+22,true)};}
  if(id==='data'){if(data)throw Error('Plusieurs blocs data');data={start:o+8,length:n};}o=end+(n&1);if(o>buffer.byteLength)throw Error('WAV padding absent');
 }
 const f=format;
 if(!f||!data||f.type!==1||f.bits!==16||![1,2].includes(f.channels)||f.align!==2*f.channels||f.byteRate!==f.sampleRate*f.align||data.length%f.align)throw Error('WAV PCM16 mono/stéréo requis');
 if(!Number.isInteger(f.sampleRate)||f.sampleRate<8000||f.sampleRate>192000||!data.length||data.length/f.align>12*f.sampleRate)throw Error('WAV : 8–192 kHz, 12 secondes maximum');
 if(!Number.isInteger(bias)||!Number.isInteger(amplitude)||amplitude<0||bias-amplitude<0||bias+amplitude>4095)throw Error('Polarisation/amplitude hors ADC12');
 const codes=new Uint16Array(data.length/f.align);
 for(let i=0;i<codes.length;i++){let sum=0;for(let c=0;c<f.channels;c++)sum+=v.getInt16(data.start+i*f.align+2*c,true);codes[i]=Math.round(bias+amplitude*sum/f.channels/32768);}
 return {codes,sampleRate:f.sampleRate,idleCode:bias};
}
