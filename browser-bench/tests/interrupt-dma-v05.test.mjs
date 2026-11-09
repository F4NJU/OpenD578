import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {createRequire} from 'node:module';
import {WasmMachine} from '../assets/wasm-machine.mjs';
const lib=await createRequire(import.meta.url)('../vendor/unicorn_arm.js')();
test('ARM code wakes WFI through three actual SysTick handlers, returns and DMA fills CPU descriptor',async()=>{
 const m=new WasmMachine({factory:async()=>lib});try{
 await m.attach({app:new File([fs.readFileSync(new URL('../samples/irq_dma_demo.bin',import.meta.url))],'irq_dma_demo.bin')});m.reset();m.setVolume('A',1234);const state=m.run(100000);
 assert.equal(state.cpu.stop?.category,'waiting',JSON.stringify(state.cpu.stop));
 const words=new DataView(m.core.memory(0x20000000,40).buffer);assert.equal(words.getUint32(0,true),3);assert.equal(words.getUint32(4,true),0x49525133);
 assert.deepEqual(Array.from({length:4},(_,i)=>words.getUint16(32+2*i,true)),[4095,1234,4095,1234]);
 assert.equal(m.core.irqLog.length,3);assert(m.core.irqLog.every(e=>e.exception===15&&e.returned));assert(m.core.hardware.adc.total>=4);
 assert.equal(m.core._get(lib.ARM_REG_IPSR),0);assert.equal(m.core._get(lib.ARM_REG_SP),m.core.irqLog[0].frame+32);
 }finally{m.core?.close();}
});
test('NMEA input reaches ARM via timed USART1 receive and four external IRQ38 frames',async()=>{
 const m=new WasmMachine({factory:async()=>lib});try{
 await m.attach({app:new File([fs.readFileSync(new URL('../samples/uart_rx_demo.bin',import.meta.url))],'uart_rx_demo.bin')});m.reset();assert.equal(m.run(10000).cpu.stop?.category,'waiting');m.gpsInject('$GPX');const s=m.run(100000);assert.equal(s.cpu.stop?.category,'waiting',JSON.stringify(s.cpu.stop));
 const b=m.core.memory(0x20000000,40),v=new DataView(b.buffer);assert.equal(v.getUint32(0,true),4);assert.equal(v.getUint32(4,true),0x55415254);assert.equal(new TextDecoder().decode(b.slice(32,36)),'$GPX');assert.equal(m.core.irqLog.length,4);assert(m.core.irqLog.every(e=>e.exception===54&&e.returned));
 }finally{m.core?.close();}
});
test('exception from PSP uses a separate MSP handler stack and restores both banks',async()=>{
 const m=new WasmMachine({factory:async()=>lib});try{
 await m.attach({app:new File([fs.readFileSync(new URL('../samples/irq_psp_demo.bin',import.meta.url))],'irq_psp_demo.bin')});m.reset();const s=m.run(100000);assert.equal(s.cpu.stop?.category,'waiting',JSON.stringify(s.cpu.stop));
 const v=new DataView(m.core.memory(0x20000000,8).buffer);assert.equal(v.getUint32(0,true),3);assert.equal(v.getUint32(4,true),0x49525133);assert.equal(m.core._get(lib.ARM_REG_CONTROL)&2,2);assert.equal(m.core._get(lib.ARM_REG_MSP),0x20018000);assert.equal(m.core._get(lib.ARM_REG_PSP),m.core.irqLog[0].frame+32);assert(m.core.irqLog.every(e=>e.returned));
 }finally{m.core?.close();}
});

test('GNSS scenario wakes a sleeping ARM program through the UART interrupt',async()=>{const m=new WasmMachine({factory:async()=>lib});try{await m.attach({app:new File([fs.readFileSync(new URL('../samples/uart_rx_demo.bin',import.meta.url))],'uart_rx_demo.bin')});m.reset();assert.equal(m.run(10000).cpu.stop?.category,'waiting');m.gpsScenario({mode:'fix',latitude:48,longitude:2,utc:'2026-11-07T12:00:00Z',hertz:1});const s=m.run(100000);assert.equal(s.cpu.stop?.category,'waiting',JSON.stringify(s.cpu.stop));assert.equal(new TextDecoder().decode(m.core.memory(0x20000020,4)),'$GPR');assert(m.core.irqLog.every(e=>e.exception===54&&e.returned));}finally{m.core?.close();}});
