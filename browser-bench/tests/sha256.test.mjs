import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {SHA256,sha256File} from '../assets/sha256.mjs';
const encoder = new TextEncoder();
test('SHA-256 standard reference vectors including block boundary',()=>{
  assert.equal(new SHA256().hex(),'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855');
  assert.equal(new SHA256().update(encoder.encode('abc')).hex(),'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');
  for(const n of [55,56,63,64,65,100000]){
    const buffer=new Uint8Array(n);buffer.fill(0x61);
    assert.equal(new SHA256().update(buffer).hex(),createHash('sha256').update(buffer).digest('hex'));
  }
});
test('File streaming SHA-256 matches Node crypto',async()=>{
  const input=new Uint8Array(2*1024*1024+77);
  for(let i=0;i<input.length;i++)input[i]=i%251;
  const file=new Blob([input]);
  const actual=await sha256File(file,null,128*1024);
  assert.equal(actual,createHash('sha256').update(input).digest('hex'));
});
