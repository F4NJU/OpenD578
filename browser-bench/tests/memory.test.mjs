import test from 'node:test';
import assert from 'node:assert/strict';
import { MemoryBus, checkVector, FLASH_SIZE, SRAM_SIZE, parseAddress, ModelBoundary } from '../assets/memory.mjs';

function vec(sp,reset) { const b=new Uint8Array(20); const v=new DataView(b.buffer); v.setUint32(0,sp,true); v.setUint32(4,reset,true);return b; }
test('Flash 3MiB, SRAM 96KiB, boot alias and load guards', () => {
  const bus=new MemoryBus();
  assert.equal(bus.flash.length,FLASH_SIZE);assert.equal(bus.sram.length,SRAM_SIZE);
  const data=vec(0x20018000,0x08006009);
  bus.loadFlash(data,0x08000000,'boot');
  assert.equal(bus.read32(0x08000000),0x20018000);
  assert.equal(bus.read32(0),0x20018000);
  assert.equal(bus.read32(0x00000004),0x08006009);
  assert.equal(bus.read8(0x082fffff),0xff);
  assert.throws(()=>bus.loadFlash(data,0x08300000),/hors Flash/);
  assert.throws(()=>bus.write32(0x08000000,0),e=>e.category==='model_incomplete');
});
test('SRAM byte/word operations and hard physical boundaries', () => {
  const bus=new MemoryBus();
  bus.write32(0x20017ffc,0x12345678);
  assert.equal(bus.read32(0x20017ffc),0x12345678);
  assert.equal(bus.read8(0x20017ffc),0x78);
  assert.equal(bus.read16(0x20017ffe),0x1234);
  assert.throws(()=>bus.read32(0x20018000),ModelBoundary);
  assert.throws(()=>bus.read8(0x40000000),e=>e.category==='model_incomplete');
  assert.throws(()=>bus.read32(0x20017ffe),e=>e.category==='execution_boundary');
  assert.throws(()=>bus.readBlock(0x20000000,257),/256/);
});
test('vecteurs and addresses are not silently normalized', () => {
  assert.ok(checkVector(vec(0x20018000,0x08006009),0x08006000).ok);
  assert.ok(!checkVector(vec(0xffffffff,0x08006008),0x08006000).ok);
  assert.equal(parseAddress('0x08006000'),0x08006000);
  assert.throws(()=>parseAddress('0xFFFFFFFFF'),/32 bits/);
  assert.throws(()=>parseAddress('NaN'),/invalide/);
});
