const assert=require('node:assert/strict');
const {MiniCps,channels,rename,same}=require('./mini_cps_protocol.js');
function fixture(){const p=new Uint8Array(2048);p.set([0x14,0x55,0,0,0,0x06,0,0,0x40]);p.set(Buffer.from('TEST'),35);return p;}
(async()=>{
const p=fixture();assert.equal(channels(p)[0].rx,145500000);assert.equal(channels(p)[0].tx,146100000);
const modified=rename(p,{0:'NEW NAME'});assert.equal(channels(modified)[0].name,'NEW NAME');
assert(p.every((v,i)=>v===modified[i]||(i>=35&&i<51)));assert.equal(channels(p)[0].name,'TEST');
assert.throws(()=>rename(p,{0:'é'}));assert.throws(()=>rename(p,{1:'NEW'}));assert.throws(()=>rename(p,{0:' '.repeat(16)}));assert.throws(()=>rename(p,{0:'X'.repeat(17)}));
const c=new MiniCps(()=>{});c.readPage=async()=>p.slice();let count=0;c.exchange=async()=>{count++;return [6];};c.programming=true;
await c.writePage(0,p,modified);assert.equal(count,129);assert(!c.programming);
count=0;const stale=p.slice();stale[0]^=1;await assert.rejects(c.writePage(0,stale,modified),/Mémoire modifiée/);assert.equal(count,0);
const bad=modified.slice();bad[0]^=1;await assert.rejects(c.writePage(0,p,bad),/Seuls les noms/);assert.equal(count,0);
c.programming=true;c.exchange=async()=>{throw Error('timeout');};await assert.rejects(c.end());assert(!c.programming,'END must not be repeated after ambiguous failure');
console.log('Mini CPS: names, BCD/offset, preservation, stale snapshot, restricted writes, END passed');
})().catch(e=>{console.error(e);process.exit(1);});
