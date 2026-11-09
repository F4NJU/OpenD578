import test from 'node:test';
import assert from 'node:assert/strict';
import {UnicornCortexM4,ownsSystemMmio,CORE_REVISION} from '../assets/unicorn-cortex.mjs';
import {RCU_BASE,FMC_BASE} from '../assets/startup-peripherals.mjs';
import {GPIO_BASE} from '../assets/board-io.mjs';
import {readFile} from 'node:fs/promises';

class NativeStub {
  constructor(){this.hooks=[];this.writes=new Map();this.registers=new Map();}
  ctl_set_cpu_model(id){this.model=id;} ctl_get_cpu_model(){return this.model;}
  mem_map(){}
  mem_write(address,bytes){this.writes.set(address>>>0,Uint8Array.from(bytes));}
  hook_add(kind,cb,userData,start,end){this.hooks.push({kind,cb,start,end});return this.hooks.length;}
  reg_read_i32(n){return this.registers.get(n)??0;}
  reg_write_i32(n,v){this.registers.set(n,v);}
  close(){}
}
const lib={Unicorn:NativeStub,ARCH_ARM:1,CPU_ARM_CORTEX_M4:9,MODE_THUMB:16,MODE_MCLASS:32,PROT_ALL:7,
 ARM_REG_SP:13,ARM_REG_LR:14,ARM_REG_PC:15,ARM_REG_XPSR:17,
 HOOK_MEM_READ:0x400,HOOK_MEM_WRITE:0x800};

test('RCU ownership stays in startup model, not legacy board IO',()=>{
  assert.equal(CORE_REVISION,'web0151r3');
  assert(ownsSystemMmio(RCU_BASE));
  assert(ownsSystemMmio(RCU_BASE+4));
  assert(ownsSystemMmio(FMC_BASE));
  assert(!ownsSystemMmio(GPIO_BASE.A));
});
test('real hook dispatch for RCU read/write never invokes BoardIO',()=>{
  const c=new UnicornCortexM4(lib);
  const read=c.uc.hooks.find(h=>h.kind===lib.HOOK_MEM_READ).cb;
  const write=c.uc.hooks.find(h=>h.kind===lib.HOOK_MEM_WRITE).cb;
  c.board.read=()=>{throw new Error('BUG: BoardIO must not handle RCU');};
  c.board.write=()=>{throw new Error('BUG: BoardIO must not handle RCU');};
  read(c.uc,17,RCU_BASE,4,0,undefined);
  assert.equal(c.uc.writes.get(RCU_BASE)[0],0x83);
  assert.equal(c.uc.writes.get(RCU_BASE)[1],0);
  write(c.uc,18,RCU_BASE,4,0x00010001,undefined);
  read(c.uc,17,RCU_BASE,4,0,undefined);
  const bytes=c.uc.writes.get(RCU_BASE);
  const ctl=(bytes[0]|(bytes[1]<<8)|(bytes[2]<<16)|(bytes[3]<<24))>>>0;
  assert.equal(ctl&(1<<16),1<<16);
  assert.equal(ctl&(1<<17),1<<17);
  assert.equal(c.modelError,null);
});
test('unknown system register stays an explicit error, without guessed zeros',()=>{
  const c=new UnicornCortexM4(lib);
  const read=c.uc.hooks.find(h=>h.kind===lib.HOOK_MEM_READ).cb;
  read(c.uc,17,RCU_BASE+0x94,4,0,undefined);
  assert.match(c.modelError?.reason??'',/RCU lecture non modelisee/);
  assert.equal(c.modelError?.address,RCU_BASE+0x94);
});
test('source graph and index request web0151r3 worker and modules',async()=>{
  const base=new URL('../',import.meta.url);
  for(const file of ['index.html','assets/app.mjs','assets/engine.wasm.worker.js','assets/engine.wasm.worker.mjs','assets/wasm-machine.mjs','assets/unicorn-cortex.mjs']){
    const s=await readFile(new URL(file,base),'utf8');
    assert.match(s,/web0151r3/,`${file} missing build marker`);
  }
});
