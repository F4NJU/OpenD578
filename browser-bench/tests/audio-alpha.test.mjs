import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createRequire} from 'node:module';
import {WasmMachine} from '../assets/wasm-machine.mjs';
const lib=await createRequire(import.meta.url)('../vendor/unicorn_arm.js')();
test('independent ARM audio alpha acquires pots/keys, draws LCD and drives real serial gain/mute waveforms without RF commands',async()=>{
 const m=new WasmMachine({factory:async()=>lib});
 try{
  await m.attach({app:new File([fs.readFileSync(new URL('../samples/audio_alpha.bin',import.meta.url))],'audio_alpha.bin')});
  m.reset();m.setVolume('A',4095);m.setVolume('B',1800);
  const channels=()=>m.board.volumeChip.status().channels;
  const run=n=>{const s=m.run(n);assert(!s.cpu.stop||s.cpu.stop.category==='waiting',JSON.stringify(s.cpu.stop));};
  const until=predicate=>{for(let i=0;i<400;i++){run(30000);if(predicate())return;}assert.fail('No expected peripheral response within bounded CPU execution');};
  until(()=>m.board.lcd.writes===20480&&channels().every(c=>c.known));
  assert.equal(channels()[0].attenuationDb,0);assert.equal(channels()[1].attenuationDb,23);assert.equal(m.board.lcd.displayOn,true);
  m.volumePcmInput({sampleRate:48000,channels:[{port:1,samples:new Float32Array(576000).fill(.5)},{port:2,samples:new Float32Array(576000).fill(-.5)}]});
  run(1000);assert.equal(m.volumePcmCapture().channels[0].samples[0],.5);
  const oldPixels=m.board.lcd.writes;
  m.setVolume('A',1800);until(()=>channels()[0].attenuationDb===23&&m.board.lcd.writes>=oldPixels+2560);
  assert.equal(m.board.lcd.writes,oldPixels+2560,'one changed volume redraws one 16-pixel band');
  m.setKey('P1',true);until(()=>channels()[0].mute);assert.equal(channels()[1].mute,false);run(100000);assert.equal(channels()[0].mute,true);m.setKey('P1',false);run(10000);
  m.setKey('P4',true);until(()=>channels()[1].mute);m.setKey('P4',false);run(10000);
  m.setKey('EXIT',true);until(()=>channels().every(c=>!c.mute&&c.attenuationDb===23));m.setKey('EXIT',false);run(10000);
  m.setKey('MENU',true);until(()=>channels().every(c=>c.mute)&&!!(m.board.out.A&128));m.setKey('MENU',false);run(10000);
  m.setKey('EXIT',true);until(()=>!(m.board.out.A&128)&&channels().every(c=>!c.mute));
  const pcm=m.volumePcmCapture();
  assert(pcm.channels[0].samples.some(x=>x===0));assert(pcm.channels[0].samples.some(x=>x>0&&x<.1));assert(pcm.channels[1].samples.some(x=>x===0));
  assert(m.core.hardware.adc.total>4);assert.equal(m.core.hardware.rf.total,0);assert.equal(m.board.out.E&64,0);assert.equal(m.board.out.C&16,0);assert.equal(m.core.hardware.dac[0x42c],0);
 }finally{m.core?.close();}
});
