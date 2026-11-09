import test from 'node:test';
import assert from 'node:assert/strict';
import {UnicornCortexM4,CORE_REVISION} from '../assets/unicorn-cortex.mjs';
import {FLASH_START,SRAM_START} from '../assets/memory.mjs';
import {RCU_BASE} from '../assets/startup-peripherals.mjs';
class CPU {
 constructor(){this.hooks=[];this.mem=new Map();this.reg=new Map();this.stopped=false;}
 ctl_set_cpu_model(id){this.model=id;} ctl_get_cpu_model(){return this.model;} mem_map(){}
 mem_write(a,data){this.mem.set(a>>>0,Array.from(data));}
 hook_add(k,cb,userData,a,b){this.hooks.push({k,cb,a,b});return this.hooks.length;}
 emu_stop(){this.stopped=true;}
 reg_read_i32(n){return this.reg.get(n)??0;}
 reg_write_i32(n,v){this.reg.set(n,v);}
}
const api={Unicorn:CPU,ARCH_ARM:1,CPU_ARM_CORTEX_M4:9,MODE_THUMB:16,MODE_MCLASS:32,PROT_ALL:7,
 ARM_REG_SP:13,ARM_REG_LR:14,ARM_REG_PC:15,ARM_REG_XPSR:17,
 HOOK_MEM_READ:0x400,HOOK_MEM_WRITE:0x800};
test('unexpected callback on bootloader Flash does not become MMIO error',()=>{
 const c=new UnicornCortexM4(api);
 const rd=c.uc.hooks.find(x=>x.k===api.HOOK_MEM_READ).cb;
 const wr=c.uc.hooks.find(x=>x.k===api.HOOK_MEM_WRITE).cb;
 for(const addr of [0x08000500,FLASH_START,SRAM_START,0x00000500]) {
  rd(c.uc,17,addr,4,0,null);wr(c.uc,18,addr,4,0x12345678,null);
 }
 assert.equal(c.modelError,null);
 assert.equal(c.uc.stopped,false);
 assert.equal(c.uc.mem.has(0x08000500),false);
 assert.equal(CORE_REVISION,'web0151r5');
});
test('RCU read still reaches the actual RCU model',()=>{
 const c=new UnicornCortexM4(api);
 const rd=c.uc.hooks.find(x=>x.k===api.HOOK_MEM_READ).cb;
 rd(c.uc,17,RCU_BASE,4,0,null);
 assert.equal(c.modelError,null);
 assert.deepEqual(c.uc.mem.get(RCU_BASE).slice(0,2),[0x83,0]);
});
test('unknown register within a peripheral remains an explicit error',()=>{
 const c=new UnicornCortexM4(api);
 const rd=c.uc.hooks.find(x=>x.k===api.HOOK_MEM_READ).cb;
 rd(c.uc,17,RCU_BASE+0x94,4,0,null);
 assert.match(c.modelError.reason,/non modelisee/);
});
