import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {audioControlStatus,audioControlText} from '../assets/audio-routing.mjs';
import {REFERENCE_FLASH_SHA} from '../assets/calibration-status.mjs';
const board=(output=0,mode=3)=>({out:{A:output},mode:()=>mode});
const rf=(word,written=true)=>({regs:new Map([['1:0:37',word]]),written:new Set(written?['1:0:37']:[])});
test('logical audio command decoding preserves unknown outputs and restricts named links to the reference Flash',()=>{
 const s=audioControlStatus(board(0,4),rf(0,false),REFERENCE_FLASH_SHA);assert.equal(s.raw.PA7,null);assert.equal(s.commands.radioSpeakerMuted,null);assert.equal(s.commands.microphoneSpeakerMuted,null);assert.equal(s.commands.pathSelector7,null);assert.match(audioControlText(s),/non reçu/);
 const other=audioControlStatus(board(128),rf(0x14),'other image');assert.equal(other.commands,null);assert.equal(other.raw.PA7,true);assert.equal(other.raw.bits[4],true);assert.match(audioControlText(other),/profil des liaisons non établi/);
});
test('six prior OEM command observations retain the speaker mutes and both MAIN/SUB bit7 values without accessing guest state',()=>{
 const observations=JSON.parse(fs.readFileSync(new URL('./fixtures/audio-routing-oem.json',import.meta.url)));
 for(const o of observations){
  assert.equal(o.harnessOEMStateWrites,false);
  const regs=rf(o.RFPIO25),before=[...regs.regs],s=audioControlStatus(board(o.GPIOoutputs.A),regs,REFERENCE_FLASH_SHA);
  assert.equal(s.commands.radioSpeakerMuted,o.expectedRadioMute,o.name);assert.equal(s.commands.microphoneSpeakerMuted,o.expectedMicMute,o.name);
  assert.equal(s.raw.bank1Page0Reg25,o.RFPIO25);assert.equal(s.effectiveReceiverAtMicrophone,null);assert.equal(s.PCMConnected,false);assert.equal(s.guestStateAccess,false);assert.deepEqual([...regs.regs],before);
 }
 const sub=observations.find(x=>x.name==='Both_verified'),main=observations.find(x=>x.name==='mic_MAIN_verified');
 assert.equal(sub.observedSettings.micPath,1);assert.equal(main.observedSettings.micPath,0);assert.equal(main.RFPIO25^sub.RFPIO25,128);
});
test('PIO bit2 is a contextual gate and never masquerades as the effective receiver or a saved menu selection',()=>{
 for(let word=0;word<256;word++){
  const s=audioControlStatus(board(),rf(0xa500|word),REFERENCE_FLASH_SHA);
  assert.equal(s.commands.routeGate2,!!(word&4));assert.equal(s.commands.pathSelector7,!!(word&128));assert.equal(s.effectiveReceiverAtMicrophone,null);
  assert.match(s.commands.selectorMeaning,/Other OEM routines may override/);assert.match(s.commands.gateMeaning,/not a fixed A\/B/);
 }
});
