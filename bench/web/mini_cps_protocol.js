/* AnyTone block protocol. No direct access to NAND or emulated MCU memory. */
(function(root){
'use strict';
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const hex=bytes=>Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
const unhex=text=>Uint8Array.from((text||'').match(/../g)||[],v=>parseInt(v,16));
const same=(a,b)=>a.length===b.length&&a.every((v,i)=>v===b[i]);
function addressBytes(address){return [address>>>24,(address>>>16)&255,(address>>>8)&255,address&255];}
function bcd(bytes){let n=0;for(const b of bytes){if((b>>4)>9||(b&15)>9)return null;n=n*100+(b>>4)*10+(b&15);}return n*10;}
function channels(page){
 if(page.length!==2048)throw Error('Page mémoire incomplète');
 return Array.from({length:32},(_,i)=>{
  const r=page.slice(i*64,(i+1)*64),nameBytes=r.slice(35,51),end=nameBytes.indexOf(0);
  const raw=end<0?nameBytes:nameBytes.slice(0,end);
  const editable=raw.length>0&&raw.every(b=>b>=32&&b<=126);
  const rx=bcd(r.slice(0,4)),offset=bcd(r.slice(4,8)),rep=r[8]>>6;
  return {name:editable?String.fromCharCode(...raw):'',editable,rx,tx:rx===null||offset===null||rep===3?null:rep===0?rx:rx+(rep===1?offset:-offset),mode:r[8]&3,power:(r[8]>>2)&3};
 });
}
function rename(page,names){
 const result=page.slice(),rows=channels(page);
 for(const [key,name] of Object.entries(names)){
  const i=Number(key);if(!Number.isInteger(i)||i<0||i>=32||!rows[i].editable)throw Error('Canal non modifiable');
  if(typeof name!=='string'||!/^[\x20-\x7e]{1,16}$/.test(name)||!name.trim())throw Error('Nom : 1 à 16 caractères ASCII imprimables');
  result.fill(0,i*64+35,i*64+51);for(let k=0;k<name.length;k++)result[i*64+35+k]=name.charCodeAt(k);
 }
 return result;
}
class MiniCps {
 constructor(api,progress=()=>{}){this.api=api;this.progress=progress;this.programming=false;}
 async status(){const limit=Date.now()+5000;while(true){const s=await this.api('usb/cdc?view=summary');if(!s.retryable)return s;if(Date.now()>limit)throw Error(s.error||'Suivi USB indisponible');await pause(30);}}
 async connect(){let s=await this.status();if(['disconnected','error'].includes(s.state))await this.api('usb/start',{});const limit=Date.now()+40000;while(true){s=await this.status();if(s.state==='ready')break;if(['stopped','error'].includes(s.state)||Date.now()>limit)throw Error(s.error||'USB non prêt');await pause(50);}this.engine=s.engine_instance;this.session=s.session;this.cursor=s.received_total;this.sent=s.sent_total+s.queued_bytes;}
 async exchange(bytes,length){
  await this.api('usb/write',{session:this.session,hex:hex(bytes)});this.sent+=bytes.length;
  const output=[],limit=Date.now()+20000;
  while(Date.now()<limit){
   const s=await this.api('usb/cdc?cursor='+this.cursor);
   if(s.retryable){await pause(30);continue;}
   if(s.state!=='ready'||s.session!==this.session)throw Error(s.error||'Session USB interrompue');
   if(this.cursor<s.received_base)throw Error('Débordement USB');
   output.push(...unhex(s.received_hex).slice(this.cursor-s.received_base));this.cursor=s.received_total;
   if(output.length>length)throw Error('Réponse supplémentaire : un autre client USB est peut-être actif');
   if(output.length===length&&s.sent_total>=this.sent)return Uint8Array.from(output);
   await pause(10);
  }
  throw Error('Délai USB dépassé. Écriture non répétée automatiquement. Relire avant de reprendre.');
 }
 async begin(){await this.connect();if(!same(await this.exchange(new TextEncoder().encode('PROGRAM'),3),[81,88,6]))throw Error('Réponse PROGRAM incorrecte');this.programming=true;const id=await this.exchange([2],16);if(!same(id.slice(0,8),[73,68,53,55,56,85,86,0])||id[15]!==6)throw Error('Identité D578UV non reconnue');return id;}
 async end(){if(!this.programming)return;this.programming=false;if(!same(await this.exchange([69,78,68],1),[6]))throw Error('END non acquitté');this.programming=false;}
 async readPage(index){
  if(!Number.isInteger(index)||index<0||index>3)throw Error('Page hors des 128 premiers emplacements');
  const page=new Uint8Array(2048),base=0x800000+index*2048;
  for(let offset=0;offset<2048;offset+=16){const a=addressBytes(base+offset),r=await this.exchange([82,...a,16],24);if(r[0]!==87||!same(r.slice(1,5),a)||r[5]!==16||r[23]!==6||r.slice(1,22).reduce((n,b)=>n+b,0)%256!==r[22])throw Error('Réponse mémoire invalide');page.set(r.slice(6,22),offset);this.progress('Lecture',offset+16,2048);}
  return page;
 }
 async writePage(index,original,modified){
  // Read/compare prevents overwriting edits made since the displayed snapshot.
  const fresh=await this.readPage(index);if(!same(fresh,original))throw Error('Mémoire modifiée depuis la lecture. Relire la page.');
  const allowed=new Set();for(let i=0;i<32;i++)for(let j=35;j<51;j++)allowed.add(i*64+j);
  if(modified.length!==2048||modified.some((v,i)=>v!==original[i]&&!allowed.has(i)))throw Error('Seuls les noms peuvent être modifiés');
  this.mutationStarted=true;
  for(let offset=0;offset<2048;offset+=16){const payload=[...addressBytes(0x800000+index*2048+offset),16,...modified.slice(offset,offset+16)],sum=payload.reduce((n,b)=>n+b,0)&255;if(!same(await this.exchange([87,...payload,sum,6],1),[6]))throw Error('Écriture non acquittée');this.progress('Écriture',offset+16,2048);}
  await this.end();
 }
}
const exports={MiniCps,channels,rename,same,hex,unhex};if(typeof module!=='undefined')module.exports=exports;else root.D578Cps=exports;
})(globalThis);
