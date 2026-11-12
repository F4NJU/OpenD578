import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';

/** Compare private page bytes with the bench decoder; return no channel data. */
export function compareOemPage(page, slots, referencePath) {
  const source=fs.readFileSync(referencePath,'utf8');
  const context={module:{exports:{}}};vm.runInNewContext(source,context,{timeout:1000});
  const reference=context.module.exports.channels(page);
  if(slots.length!==32)throw Error('Expected 32 decoded slots');
  const modes=['FM','DMR','FM + DMR RX','DMR + FM RX'];
  const powers=['Low','Mid','High','Turbo'];
  let conservativeUnknowns=0;
  reference.forEach((row,index)=>{
    const normalized={name:row.editable?row.name:null,rxHz:row.rx>0?row.rx:null,
      txHz:row.tx>0?row.tx:null,mode:modes[row.mode],power:powers[row.power]};
    if(row.rx===0||row.tx!==null&&row.tx<=0)conservativeUnknowns++;
    for(const field of Object.keys(normalized)){
      if(slots[index][field]!==normalized[field])throw Error(`Decoder mismatch at slot ${index+1}, field ${field}`);
    }
  });
  return {comparedSlots:32,comparedFieldsPerSlot:5,mismatches:0,conservativeUnknowns,
    referenceSha256:crypto.createHash('sha256').update(source).digest('hex')};
}

/** Reassemble only replies observed on the real client's HTTP/USB transport. */
export function pageFromReplies(received) {
  const start=Math.min(...received.keys());
  const length=3+16+128*24+1;
  const stream=Uint8Array.from({length},(_,index)=>{
    if(!received.has(start+index))throw Error('Incomplete captured USB replies');
    return received.get(start+index);
  });
  if(stream[0]!==81||stream[1]!==88||stream[2]!==6||stream.at(-1)!==6)throw Error('Unexpected session boundaries');
  const page=new Uint8Array(2048);
  for(let block=0;block<128;block++){
    const frame=stream.slice(19+block*24,19+(block+1)*24);
    const address=frame[1]*0x1000000+(frame[2]<<16)+(frame[3]<<8)+frame[4];
    if(frame[0]!==87||address!==0x800000+block*16||frame[5]!==16||frame[23]!==6||
      (frame.slice(1,22).reduce((n,b)=>n+b,0)&255)!==frame[22])throw Error('Invalid observed page-zero reply');
    page.set(frame.slice(6,22),block*16);
  }
  return page;
}
