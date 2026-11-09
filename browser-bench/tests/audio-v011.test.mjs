import test from 'node:test';import assert from 'node:assert/strict';
import {U2429,Aic3204ControlObserver,SctAudioControl,audioStatusText} from '../assets/audio-devices.mjs';
import {BoardIO,GPIO_BASE,AFIO} from '../assets/board-io.mjs';
import {SctHpi} from '../assets/radio-buses.mjs';
// Firmware-style serial waveforms. Fixed words below come from UTC's table,
// independent of the production decoder and of the historical C encoder.
function driveWord(send,word,count=11,latch=true){let state=0;const set=v=>{send(state,v);state=v;};for(let bit=0;bit<count;bit++){
 const data=(word>>>bit)&1?0x2000:0;set(data);set(data|0x4000);
 if(bit===count-1&&latch){set(data);}else{set(0x4000);set(0);}set(0);
}}
test('UTC D0 selects channel and D1 selects individual/common; no update before final latch',()=>{
 const d=new U2429(),send=(a,b)=>d.gpio(a,b,123);
 assert.throws(()=>d.process(1,[1]),/not yet latched/);
 driveWord(send,0x7d6,11,false);assert.equal(d.accepted,0);
 d.disconnect();driveWord(send,0x7d6);assert.deepEqual(d.channels.map(c=>c?.attenuationDb??null),[0,null]);
 driveWord(send,0x607);assert.equal(d.channels[1].attenuationDb,83);assert.equal(d.channels[0].attenuationDb,0);
 driveWord(send,0x7d4);assert.deepEqual(d.channels.map(c=>c.attenuationDb),[0,0]);
 driveWord(send,0x602);assert.equal(d.channels[0].mute,true);assert.equal(d.channels[1].mute,false);
 assert.equal(d.frames.at(-1).time,123);
});
test('invalid/partial U2429 latch retains previous gain; raw component attenuation has correct amplitude',()=>{
 const d=new U2429(),send=(a,b)=>d.gpio(a,b);driveWord(send,0x606); // CH1 -83dB
 const expected=10**(-83/20),out=d.process(1,[-0.5,0,0.5]);assert(Math.abs(out[2]/0.5-expected)<1e-10);assert.equal(out[0],-out[2]);
 const old=d.channels[0];driveWord(send,0x602,10);assert.equal(d.channels[0],old);assert.equal(d.rejected,1);
 driveWord(send,0x67e);assert.equal(d.rejected,2);assert.equal(d.channels[0],old); // coarse=31 reserved
 driveWord(send,0x602);assert.deepEqual([...d.process(1,[1,-1,0.25])],[0,-0,0]);
 assert.throws(()=>d.process(0,[1]),RangeError);
});
test('only configured PA13/PA14 GPIO edges drive the external volume IC; MCU reset preserves latched state',()=>{
 const b=new BoardIO(),send=(a,v)=>b.write(GPIO_BASE.A+12,v);
 driveWord(send,0x7d6);assert.equal(b.volumeChip.accepted,0);
 b.write(GPIO_BASE.A+4,0x43344444);driveWord(send,0x7d6);assert.equal(b.volumeChip.accepted,0);
 b.write(AFIO+4,0x04000000);driveWord(send,0x7d6);assert.equal(b.volumeChip.channels[0].attenuationDb,0);
 const device=b.volumeChip;b.reset({preserveExternal:true});assert.equal(b.volumeChip,device);assert.equal(b.volumeChip.channels[0].attenuationDb,0);
 b.reset();assert.equal(b.volumeChip.channels[0],null);
});
test('codec gain fields use TI signed driver / half-dB PGA coding and preserve unobserved state',()=>{
 const c=new Aic3204ControlObserver();assert.equal(c.status().drivers.HPL.known,false);
 c.write(0,1);c.write(16,0x3a);c.write(17,0x40);c.write(18,8);c.write(19,4);c.write(60,20);
 let s=c.status();assert.equal(s.drivers.HPL.gainDb,-6);assert.equal(s.drivers.HPR.mute,true);assert.equal(s.drivers.LOL.gainDb,8);assert.equal(s.drivers.LOR.gainDb,4);assert.equal(s.micPGA.right.gainDb,10);assert.equal(s.micPGA.left.known,false);
 c.write(60,0x94);assert.equal(c.status().micPGA.right.gainDb,0);
 c.write(16,31);assert.equal(c.status().drivers.HPL.gainDb,null);
 c.write(0,0);c.write(65,0x81);c.write(66,48);c.write(83,0xe8);c.write(84,40);s=c.status();
 assert.equal(s.digitalDAC.left.gainDb,-63.5);assert.equal(s.digitalDAC.right.gainDb,24);assert.equal(s.digitalADC.left.gainDb,-12);assert.equal(s.digitalADC.right.gainDb,20);
 c.write(0,8);c.write(1,19);assert.equal(c.get(8,1),19);c.write(0,0);c.write(1,1);assert.equal(c.registers.size,0);assert.equal(c.status().drivers.LOL.known,false);
});
test('SCT codec control observer follows only well-formed HPI requests without claiming hidden DSP/I2C or PCM',()=>{
 const s=new SctHpi();s.complete=true;
 const send=(kind,data)=>{const p=[132,169,97,0,data.length,kind,...data];if(p.length&1)p.push(0);for(const b of p)s.write(b);};
 send(0,[45,1]);send(64,[0,1,60,20,0,0]);
 const c=s.status().codecControl;assert.equal(c.micPGA.right.gainDb,10);assert.equal(c.codecI2cExecutionObserved,false);assert.equal(c.PCMTransportQualified,false);assert.equal(s.status().DSPExecuted,false);
});

test('TI AGC command decoding retains unknown timing; presentation does not equate PGA with a working audio path',()=>{
 const c=new Aic3204ControlObserver();c.write(86,0xa0);c.write(88,32);let s=c.status();assert.equal(s.AGC.left.targetDbFS,-10);assert.equal(s.AGC.left.maximumGainDb,16);assert.equal(s.AGC.left.attackWordClocks,null);assert.equal(s.AGC.right.enabled,null);
 c.write(89,9);c.write(90,10);s=c.status();assert.equal(s.AGC.left.attackWordClocks,192);assert.equal(s.AGC.left.decayWordClocks,6144);
 const text=audioStatusText({attenuator:new U2429().status(),codecControl:s});assert.match(text,/Canal 1 : non reçu/);assert.match(text,/PGA micro G \/ D : non reçu \/ non reçu/);assert.match(text,/Flux audio non raccordé/);assert.match(text,/gain max. 16 dB/);
});
test('documented SCT straight-form EQ preserves state across audio blocks and rejects unknown configuration/sample rate',()=>{
 const make=()=>{const c=new SctAudioControl();c.field(112,[0x31,0xe0,0,0,0,0x20,0,0,0,0,0]);for(const s of [0x22,0x23])c.field(112,[s,0,0,0,0,0,0,0,0,0,0]);return c;};
 assert.throws(()=>new SctAudioControl().processCorrection('TX',[1]),/incomplete/);
 const a=make(),b=make();assert.deepEqual([...a.processCorrection('TX',[1,0,0,0,0])],[0.5,0.25,0.125,0.0625,0.03125]);
 assert.deepEqual([...b.processCorrection('TX',[1,0]),...b.processCorrection('TX',[0,0,0])],[0.5,0.25,0.125,0.0625,0.03125]);
 assert.throws(()=>a.processCorrection('TX',[1],48000),RangeError);assert.equal(a.status().bitExactDSP,false);assert.equal(a.status().PCMRouteConnected,false);
});
test('OEM EQ coefficient bytes decode with signed Q14 and distinct RX/TX banks through HPI',()=>{
 const s=new SctHpi();s.complete=true;const send=data=>{let p=[132,169,97,0,data.length,0,...data];if(p.length&1)p.push(0);for(const b of p)s.write(b);};
 send([112,1,132,92,59,225,63,98,132,87,60,123]);send([112,49,132,92,59,225,63,98,132,87,60,123]);
 const a=s.status().audioControl;assert.equal(a.filters.RX[0].enabled,false);assert.equal(a.filters.TX[0].enabled,true);assert.equal(a.filters.TX[0].a1,-1.931884765625);assert.equal(a.filters.TX[0].b0,0.9903564453125);assert.equal(a.filters.TX[1],null);
 send([107,8,0,8,0,128,0,128,0,0,0,0,0]);assert.equal(s.status().audioControl.IQgains.IQ_TX,1);assert.equal(s.status().audioControl.IQgains.subaudioRX,16);
});
