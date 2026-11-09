import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {createRequire} from 'node:module';
import {WasmMachine} from '../assets/wasm-machine.mjs';
import {UnicornCortexM4} from '../assets/unicorn-cortex.mjs';
const lib=await createRequire(import.meta.url)('../vendor/unicorn_arm.js')();
const sample=fs.readFileSync(new URL('../samples/board_hw_demo.bin',import.meta.url));
const make=async()=>{const m=new WasmMachine({factory:async()=>lib});await m.attach({app:new File([sample],'board_hw_demo.bin')});m.reset();return m;};
test('actual WASM selects and reads back Cortex-M4',()=>{
 const c=new UnicornCortexM4(lib);assert.equal(c.cpuModelId,lib.CPU_ARM_CORTEX_M4);assert.equal(c.uc.ctl_get_cpu_model(),lib.CPU_ARM_CORTEX_M4);c.close();
});
test('actual ARM firmware writes LCD pixels, lighting and SRAM before a WFI wait state',async()=>{
 const m=await make();try{
  const result=m.run(100000);assert.equal(result.cpu.stop?.category,'waiting');assert.match(result.cpu.stop.reason,/WFI/);
  assert.equal(m.board.lcd.writes,1024);assert.equal(m.board.lcd.displayOn,true);assert.equal(m.board.lcd.sleep,false);
  assert.equal(m.board.lcdBacklight,255);assert.equal(m.board.lcd.pixels[0],0xf800);assert.equal(m.board.lcd.pixels[16],0x07e0);assert.equal(m.board.lcd.pixels[16*128],0x001f);
  assert.deepEqual([...m.core.memory(0x20000000,4)],[0x37,0x35,0x44,0x4f]);
  const stoppedPc=result.cpu.pc;m.run(100000);assert.equal(m.core.state().pc,stoppedPc);assert.equal(m.board.lcd.writes,1024);
 }finally{m.core.close();}
});
test('MCU reset preserves external keys and knob positions, clears modeled LCD and can rerun the program',async()=>{
 const m=await make();try{
  m.setKey('POWER',true);m.setKey('P1',true);m.setVolume('A',1234);m.run(100000);m.reset();
  assert.equal(m.board.input.A&1,0);assert.equal(m.board.adc.get(8),250);assert.equal(m.board.adc.get(12),1234);assert.equal(m.board.lcd.writes,0);
  assert.equal(m.run(100000).cpu.stop?.category,'waiting');assert.equal(m.board.lcd.writes,1024);
 }finally{m.core.close();}
});
test('a requested Cortex-M4 model is rejected when the backend silently substitutes another CPU',()=>{
 class WrongCPU{ctl_set_cpu_model(){}ctl_get_cpu_model(){return 11}close(){}}
 assert.throws(()=>new UnicornCortexM4({...lib,Unicorn:WrongCPU}),/ignoré le modèle/);
});
