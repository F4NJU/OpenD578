import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {createRequire} from 'node:module';
import {WasmMachine} from '../assets/wasm-machine.mjs';import {BoardIO,GPIO_BASE,AFIO,EXTI} from '../assets/board-io.mjs';import {panelStatus} from '../assets/panel-status.mjs';
const lib=await createRequire(import.meta.url)('../vendor/unicorn_arm.js')();
async function make(name){const m=new WasmMachine({factory:async()=>lib});await m.attach({app:new File([fs.readFileSync(new URL('../samples/'+name+'.bin',import.meta.url))],name+'.bin')});m.reset();return m;}
test('electrical edges only pend the AFIO-selected, CPU-enabled EXTI line; masked edge still latches',()=>{const b=new BoardIO(),irqs=[];b.hardware={m:{time:0},pend:i=>irqs.push(i)};
 const low=()=>b.driveInputs('C',b.input.C&~256),high=()=>b.driveInputs('C',b.input.C|256);
 low();assert.equal(b.regs.get(EXTI+20),0);assert.equal(irqs.length,0);
 high();b.regs.set(AFIO+16,2);b.regs.set(EXTI+12,256);low();assert.equal(b.regs.get(EXTI+20),256);assert.deepEqual(irqs,[]);
 b.write(EXTI+20,256);b.regs.set(EXTI,256);high();low();assert.deepEqual(irqs,[23]);assert.equal(b.regs.get(EXTI+20),256);
 b.write(EXTI+20,256);b.regs.set(EXTI+12,0);b.regs.set(EXTI+8,256);high();assert.equal(b.regs.get(EXTI+20),256);
 b.write(EXTI+20,256);b.regs.set(GPIO_BASE.C+4,0x44444443);low();high();assert.equal(b.regs.get(EXTI+20),0);
});
test('real ARM with both EXTI edges sees one correctly directed quadrature event per command, including queued reversal',async()=>{const m=await make('panel_irq_demo');try{assert.equal(m.run(10000).cpu.stop?.category,'waiting');
 let i=0;for(const direction of ['up','up','down','up','down','down']){m.rotate(direction);const s=m.run(10000);assert.equal(s.cpu.stop?.category,'waiting',JSON.stringify(s.cpu.stop));const v=new DataView(m.core.memory(0x20000000,12).buffer);assert.equal(v.getUint32(0,true),++i);assert.equal(v.getUint32(8,true),direction==='up'?1:0);}
 m.rotate('up');m.rotate('down');m.rotate('down');m.run(10000);const v=new DataView(m.core.memory(0x20000000,12).buffer);assert.equal(v.getUint32(0,true),9);assert.equal(v.getUint32(8,true),0);
 assert.equal(m.core.irqLog.length,9);assert(m.core.irqLog.every(e=>e.exception===39&&e.returned));assert.equal(m.core.hardware.encoderEvents.length,0);
 }finally{m.core.close();}});
test('eight resistor keys and both pots traverse the real seven-rank ARM ADC/DMA descriptor',async()=>{for(const [left,right,lv,rv,pa,pb] of [['P1','P4',250,250,0,4095],['P2','P5',1000,1000,4095,0],['P3','P6',2000,2000,321,3456],['MENU','EXIT',3000,3000,1800,1800]]){const m=await make('adc_sensors_demo');try{m.setKey(left,true);m.setKey(right,true);m.setVolume('A',pa);m.setVolume('B',pb);assert.equal(m.run(100000).cpu.stop?.category,'waiting');const v=new DataView(m.core.memory(0x20000020,14).buffer);assert.deepEqual(Array.from({length:7},(_,i)=>v.getUint16(2*i,true)),[262,lv,rv,1034,2600,pa,pb]);const p=m.status().FACADE;assert.deepEqual(p.volumes.map(x=>x.acquiredRaw),[pa,pb]);assert(p.volumes.every(x=>x.receiverGainRaw===null));assert.equal(p.audio.PCMEmulated,false);
 }finally{m.core.close();}}});
test('Power and dial push release cleanly; long panel duration uses virtual time and rejects invalid duration',async()=>{const m=await make('board_hw_demo');try{for(const key of ['POWER','DIAL_PRESS']){m.panelKey(key,true,1500);m.panelKey(key,false,1500);assert(m.board.keys.has(key));m.core.hardware.advance(179999999);assert(m.board.keys.has(key));m.core.hardware.advance(1);assert(!m.board.keys.has(key));}assert.equal(m.board.input.A&3,3);assert.throws(()=>m.panelKey('MENU',true,10001));assert.equal(m.board.adc.get(8),4095);assert.equal(panelStatus(m.board,m.core.hardware).lighting.LEDword,null);}finally{m.core.close();}});
