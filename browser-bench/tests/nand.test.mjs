import test from 'node:test';
import assert from 'node:assert/strict';
import {NandOverlay,NAND_MAIN_SIZE,NAND_OOB_SIZE,NAND_PAGES} from '../assets/nand.mjs';
const fake = (size,initial=0xff)=>({name:'test.bin',size,slice(a,b){return {async arrayBuffer(){return Uint8Array.from({length:b-a},()=>initial).buffer;}}}});
test('NAND lazily reads page 131071 without allocating 256MiB',async()=>{
  const nand=new NandOverlay();nand.attach('main',fake(NAND_MAIN_SIZE));
  const page=await nand.readPage('main',NAND_PAGES-1);
  assert.equal(page.bytes.length,2048);assert.equal(page.bytes[2047],255);
  await assert.rejects(nand.readPage('main',NAND_PAGES),/hors plage/);
  assert.throws(()=>nand.attach('oob',fake(42)),/attendu/);
});
test('programming one-way, block erase, overlay and atomic import/export',async()=>{
  const nand=new NandOverlay();nand.attach('main',fake(NAND_MAIN_SIZE));nand.attach('oob',fake(NAND_OOB_SIZE));
  await nand.program('main',3,8,Uint8Array.of(0x2a,0x00));
  assert.equal((await nand.readPage('main',3)).bytes[8],0x2a);
  await assert.rejects(nand.program('main',3,8,Uint8Array.of(0xff)),/0->1/);
  const patch=nand.exportPatch();assert.equal(patch.changes.length,1);
  const clone=new NandOverlay();clone.importPatch(patch);
  assert.equal((await clone.readPage('main',3)).bytes[8],0x2a);
  const tampered=structuredClone(patch);tampered.changes[0].base64='AA';
  assert.throws(()=>clone.importPatch(tampered),/Taille page/);
  assert.equal((await clone.readPage('main',3)).bytes[8],0x2a);
  await nand.erase(0);
  assert.equal((await nand.readPage('main',3)).bytes[8],0xff);
  assert.equal(nand.summary().overlayPages,128);
});
test('missing capture stops both CPU and explorer reads instead of returning erased bytes',async()=>{
 const n=new NandOverlay();assert.throws(()=>n.readPageSync('main',0),/Capture NAND absente/);await assert.rejects(n.readPage('main',0),/Capture NAND absente/);
});
