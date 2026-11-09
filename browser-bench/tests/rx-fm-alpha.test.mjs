import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import{createRequire}from'node:module';
import{WasmMachine}from'../assets/wasm-machine.mjs';
const lib=await createRequire(import.meta.url)('../vendor/unicorn_arm.js')();
test('independent ARM FM RX: init four banks, tune two receivers, squelch, gains, speakers, width, encoder; PTT stays inhibited',async()=>{
 const m=new WasmMachine({factory:async()=>lib});
 try{
  await m.attach({app:new File([fs.readFileSync(new URL('../samples/rx_fm_alpha.bin',import.meta.url))],'rx_fm_alpha.bin')});m.reset();m.setVolume('A',4095);m.setVolume('B',1800);
  let txGateHigh=0;const originalWrite=m.board.write.bind(m.board);m.board.write=(...args)=>{const r=originalWrite(...args);if((m.board.out.E&64)||(m.board.out.C&16))txGateHigh++;return r;};
  const run=()=>{let s=m.run(30000);assert(!s.cpu.stop||s.cpu.stop.category==='waiting',JSON.stringify(s.cpu.stop));};
  const until=p=>{for(let i=0;i<1600;i++){run();if(p())return;}assert.fail('RX peripheral response missing');};
  const rf=()=>m.core.hardware.rf,reg=(b,p,r)=>rf().regs.get(`${b}:${p}:${r}`),channels=()=>m.board.volumeChip.status().channels;
  const hz=b=>rf().frequencyCommands.committed[b]?.frequencyHz;
  until(()=>m.board.lcd.writes>=20480&&reg(1,0,3)===0xbff5&&channels().every(c=>c.known));
  assert.equal(m.core.boot.status().rcuConfig&0x003fcf0f,0x0021c40a);assert.equal(hz(0),38850000);assert.equal(hz(2),184350000);assert.equal(hz(1),38550000);assert.equal(hz(3),396450000);
  assert.equal(reg(0,0,0x44),0x43ec);assert.equal(reg(1,0,0x44),0x43ec);assert.equal(reg(0,0,0x47),0x6140);assert.equal(reg(1,0,0x47),0x6140);assert.equal(reg(0,0,0x78),0x78ff);assert.equal(reg(1,0,0x78),0x78ff);assert(channels().every(c=>c.mute));assert(m.board.out.A&128);assert(reg(1,0,0x25)&16);
  m.volumePcmInput({sampleRate:8000,channels:[{port:1,samples:new Float32Array(96000).fill(.5)},{port:2,samples:new Float32Array(96000).fill(-.5)}]});
  const input=(b,status,noise=127,level=0)=>rf().setInputs(b,{12:status,101:noise,103:level});
  input(0,2);until(()=>!channels()[0].mute&&!(m.board.out.A&128));assert.equal(channels()[0].attenuationDb,0);assert(channels()[1].mute);
  input(1,2);until(()=>!channels()[1].mute);assert.equal(channels()[1].attenuationDb,23);
  input(0,0,0,511);for(let i=0;i<10;i++)run();assert.equal(channels()[0].mute,false,'good fallback samples preserve RX');
  input(0,0,127,0);until(()=>channels()[0].mute);assert.equal(channels()[1].mute,false);
  const key=async(name,p)=>{m.setKey(name,true);for(let i=0;i<40;i++)run();until(p);m.setKey(name,false);for(let i=0;i<40;i++)run();};
  await key('P4',()=>!(reg(1,0,0x25)&16)&&!(m.board.out.A&128)); // Both after Radio
  await key('P4',()=>!(reg(1,0,0x25)&16)&&!!(m.board.out.A&128)); // Mic
  await key('P4',()=>!!(reg(1,0,0x25)&16)&&!(m.board.out.A&128)); // Radio
  await key('MENU',()=>channels().every(c=>c.mute)&&!!(m.board.out.A&128));
  await key('EXIT',()=>!channels()[1].mute&&!(m.board.out.A&128));
  await key('P2',()=>!channels()[0].mute);input(1,0); // monitor allows explicit opening without carrier
  const old=hz(2);m.board.rotate('up');until(()=>hz(2)===old+12500&&reg(0,0,3)===0xbff5);assert(m.core.irqLog.some(x=>x.exception===39&&x.returned));
  await key('P1',()=>m.board.lcd.writes>0); // Select B; subsequent encoder IRQ must tune bank3 only.
  const beforeB=hz(3);m.board.rotate('down');until(()=>hz(3)<beforeB&&reg(1,0,3)===0xbff5);
  await key('P1',()=>true); // back to A, release debounce occurs in key helper
  await key('P5',()=>reg(0,0,0x3a)===0xe0&&reg(0,0,3)===0xbff5);assert.equal(reg(0,1,0x1b),4);
  await key('P3',()=>hz(2)===396150000&&reg(0,0,3)===0xbff5);assert.equal(hz(0),38850000);
  const txBefore=[m.board.out.E&64,m.board.out.C&16,m.core.hardware.dac[0x42c]??0];m.micPress({ptt:true});for(let i=0;i<40;i++)run();assert.deepEqual([m.board.out.E&64,m.board.out.C&16,m.core.hardware.dac[0x42c]??0],txBefore);assert.deepEqual(txBefore,[0,0,0]);
  const pcm=m.volumePcmCapture();assert(pcm.channels[0].samples.some(x=>x===.5));assert(pcm.channels[0].samples.some(x=>x===0));assert(pcm.channels[1].samples.some(x=>x<0&&x>-.1));
  assert.equal(reg(0,0,3),0xbff5);assert.equal(reg(1,0,3),0xbff5);assert.equal(txGateHigh,0);assert.equal(m.board.red,false);assert.equal(m.board.green,true);
 }finally{m.core?.close();}
});
