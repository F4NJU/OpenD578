import test from 'node:test';
import assert from 'node:assert/strict';
import {UnicornCortexM4} from '../assets/unicorn-cortex.mjs';
import {FLASH_START,FLASH_SIZE,SRAM_START} from '../assets/memory.mjs';
import {GPIO_BASE} from '../assets/board-io.mjs';
class FakeNativeUnicorn {
  constructor(){this.cpuModel=null;this.regs=new Map();this.mappings=[];this.chunks=new Map();this.hooks=[];this.emulations=[];}
  ctl_set_cpu_model(id){this.cpuModel=id;} ctl_get_cpu_model(){return this.cpuModel;}
  mem_map(addr,size){this.mappings.push({addr,size});}
  mem_write(addr,data){this.chunks.set(addr,Uint8Array.from(data));}
  mem_read(addr,n){const x=this.chunks.get(addr);return x?.subarray(0,n)??new Uint8Array(n);}
  reg_write_i32(id,n){this.regs.set(id,n>>>0);}
  reg_read_i32(id){return this.regs.get(id)??0;}
  hook_add(kind,callback,userData,first,last){this.hooks.push({kind,callback,first,last});}
  emu_start(pc,until,timeout,count){this.emulations.push({pc,until,count});this.regs.set(15,pc+4);}
  close(){}
}
const library={Unicorn:FakeNativeUnicorn,ARCH_ARM:1,MODE_THUMB:16,MODE_MCLASS:32,PROT_ALL:7,
 ARM_REG_SP:13,ARM_REG_LR:14,ARM_REG_PC:15,ARM_REG_CPSR:16,ARM_REG_XPSR:17,CPU_ARM_CORTEX_M4:9,HOOK_MEM_WRITE:2048,HOOK_MEM_READ:1024};
for(let i=0;i<=12;i++)library[`ARM_REG_R${i}`]=i;
test('Unicorn backend maps physical GD32 ranges and loads real vector table',()=>{
 const c=new UnicornCortexM4(library),bytes=new Uint8Array(FLASH_SIZE).fill(0xff);
 bytes.set([0x00,0x80,0x01,0x20,0x01,0x60,0x00,0x08],0);c.loadFlash(bytes);
 const reset=c.reset(FLASH_START);assert.equal(reset.stack,0x20018000);
 assert.equal(c.uc.reg_read_i32(13),0x20018000);
 assert.equal(c.uc.cpuModel,9);
 assert.equal(c.uc.reg_read_i32(17),0x01000000);
 assert.equal(c.uc.reg_read_i32(15),0x08006000);
 assert(c.uc.mappings.some(m=>m.addr===FLASH_START&&m.size===FLASH_SIZE));
 assert(c.uc.mappings.some(m=>m.addr===SRAM_START));
 assert(c.uc.hooks.some(h=>h.first===0x420d8000));assert(c.uc.hooks.some(h=>h.first===0x420e0000));
 assert(c.uc.chunks.get(0x08000000)[4]===1);
});
test('WASM dispatch uses ARM emu_start, not hand-decoding Thumb16',()=>{
 const c=new UnicornCortexM4(library),bytes=new Uint8Array(FLASH_SIZE).fill(0xff);
 bytes.set([0x00,0x80,0x01,0x20,0x01,0x60,0x00,0x08]);c.loadFlash(bytes);c.reset();c.run({budget:5000});
 assert.equal(c.uc.emulations[0].count,5000);
 assert.equal(c.uc.emulations[0].pc,0x08006001);
});
test('peripheral hooks dispatch physical GPIO register write to board without OEM variables',()=>{
 const c=new UnicornCortexM4(library),cb=c.uc.hooks.find(h=>h.kind===2048).callback;
 cb(c.uc,17,GPIO_BASE.E+0x0c,4,8,0);assert.equal(c.board.out.E,8);
});
test('unsupported native Unicorn binding fails instead of silently falling back to Thumb16',()=>{
 assert.throws(()=>new UnicornCortexM4({...library,HOOK_MEM_WRITE:undefined}),/hooks/);
});
