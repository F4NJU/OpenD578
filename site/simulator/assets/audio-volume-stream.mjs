/* Explicit U2429 INn -> OUTn transfer. Not an assumed RF/speaker network. */
export class AudioVolumeStream {
 constructor(chip){this.chip=chip;this.clear();}
 clear(){this.source=null;this.output=[];this.count=0;this.changes=0;}
 configure({channels,sampleRate},now){
  if(!Array.isArray(channels)||!channels.length||channels.length>2||!Number.isInteger(sampleRate)||sampleRate<8000||sampleRate>192000||!Number.isSafeInteger(now)||now<0)throw Error('PCM U2429 : ports explicites, 8–192 kHz');
  const ports=new Set();let length=null;
  for(const c of channels){if(![1,2].includes(c.port)||ports.has(c.port)||!c.samples||!Number.isInteger(c.samples.length)||c.samples.length<1||c.samples.length>12*sampleRate)throw Error('PCM U2429 : port ou durée invalide');ports.add(c.port);if(length!==null&&length!==c.samples.length)throw Error('Longueurs PCM différentes');length=c.samples.length;if(!this.chip.channels[c.port-1])throw Error(`U2429 canal ${c.port} : régler le volume par le firmware avant cet essai`);for(const x of c.samples)if(!Number.isFinite(x)||Math.abs(x)>1)throw Error('PCM hors -1..1');}
  this.source={channels:channels.map(c=>({port:c.port,samples:Float32Array.from(c.samples)})),sampleRate,start:now,length};this.output=channels.map(()=>new Float32Array(length));this.count=0;this.changes=0;
 }
 advance(now){const s=this.source;if(!s)return;if(!Number.isFinite(now)||now<s.start)throw Error('Temps audio invalide');const end=Math.min(s.length,Math.ceil((now-s.start)*s.sampleRate/120000000));if(end<=this.count)return;
  for(let c=0;c<s.channels.length;c++){const channel=s.channels[c],state=this.chip.channels[channel.port-1];if(!state)throw Error('Gain U2429 inconnu');for(let i=this.count;i<end;i++)this.output[c][i]=channel.samples[i]*state.gain;}this.count=end;
 }
 beforeLatch(now){if(this.source){this.advance(now);this.changes++;}}
 capture(now){this.advance(now);if(!this.source||!this.count)throw Error('Exécuter le firmware pour faire avancer le temps audio');return {sampleRate:this.source.sampleRate,channels:this.output.map((s,i)=>({port:this.source.channels[i].port,samples:s.slice(0,this.count)})),status:this.status()};}
 status(){return {connected:!!this.source,ports:this.source?.channels.map(c=>`IN${c.port} → OUT${c.port}`)??[],sampleRate:this.source?.sampleRate??null,total:this.source?.length??0,processed:this.count,gainChanges:this.changes,source:'explicit U2429 component inputs',nominalSmallSignalTransfer:true,RFvoiceInputConnected:false,speakerNetsConnected:false,timing:'120M virtual units/s; not cycle accurate'};}
}
export function pcm16Wav(channels,sampleRate){
 if(!Array.isArray(channels)||![1,2].includes(channels.length)||!Number.isInteger(sampleRate)||sampleRate<8000||sampleRate>192000)throw Error('WAV sortie invalide');const length=channels[0].length;if(!length||length>12*sampleRate||channels.some(c=>c.length!==length))throw Error('WAV longueur invalide');
 const buffer=new ArrayBuffer(44+2*length*channels.length),v=new DataView(buffer),str=(o,s)=>[...s].forEach((c,i)=>v.setUint8(o+i,c.charCodeAt(0)));str(0,'RIFF');v.setUint32(4,buffer.byteLength-8,true);str(8,'WAVEfmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,channels.length,true);v.setUint32(24,sampleRate,true);v.setUint32(28,sampleRate*channels.length*2,true);v.setUint16(32,channels.length*2,true);v.setUint16(34,16,true);str(36,'data');v.setUint32(40,buffer.byteLength-44,true);
 for(let i=0;i<length;i++)for(let c=0;c<channels.length;c++){const x=channels[c][i];if(!Number.isFinite(x))throw Error('PCM non fini');v.setInt16(44+2*(i*channels.length+c),Math.max(-32768,Math.min(32767,Math.round(x*32768))),true);}return buffer;
}
