import test from 'node:test';
import assert from 'node:assert/strict';
import {UnicornCortexM4} from '../assets/unicorn-cortex.mjs';
class ABI {
 constructor(){this.hooks=[];}
 mem_map(){} ctl_set_cpu_model(id){this.model=id;} ctl_get_cpu_model(){return this.model;}
 hook_add(type,callback,userData,begin,end){
  assert.equal(arguments.length,5,'Unicorn.js requires explicit user_data before begin/end');
  assert.equal(userData,null);assert.equal(typeof begin,'number');assert.equal(typeof end,'number');
  const hook={type,callback,begin,end};this.hooks.push(hook);return hook;
 }
}
const lib={Unicorn:ABI,ARCH_ARM:1,CPU_ARM_CORTEX_M4:9,ARM_REG_PC:15,MODE_THUMB:16,MODE_MCLASS:32,PROT_ALL:7,
 HOOK_MEM_READ:0x400,HOOK_MEM_WRITE:0x800,HOOK_MEM_INVALID:0x3f0,HOOK_CODE:4};
test('memory hooks use the real five-argument ABI and exclude Flash/SRAM',()=>{
 const c=new UnicornCortexM4(lib,{debug:true});
 const hw=c.uc.hooks.filter(h=>h.type===0x400||h.type===0x800);
 assert.equal(hw.filter(h=>h.begin>=0x40000000).length,10);assert.equal(hw.filter(h=>h.begin===0x082f5000).length,1);
 for(const h of hw){assert(h.begin<=h.end);assert(h.begin>=0x40000000||h.begin===0x082f5000);}
 assert.equal(c.uc.hooks.find(h=>h.type===lib.HOOK_CODE).begin,1);
 assert.equal(c.uc.hooks.find(h=>h.type===lib.HOOK_CODE).end,0);
});
