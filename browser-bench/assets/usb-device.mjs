/* GD32 single-buffer USBD/PMA, port of V11 usbd_host.py. Host tokens never
 * read Flash/SRAM/NAND. Every response payload is read from firmware PMA. */
import {UsbIdle} from './timed-devices.mjs?build=web0151r5';
export class UsbDevice extends UsbIdle{
 constructor(enabled=()=>true){super();this.enabled=enabled;this.connected=false;this.enumerated=false;this.tokens=[];this.totalTokens=0;this.lastResponse=null;}
 flags(){let f=this.r[0x44]&0x7f00;for(let e=0;e<8;e++){const v=this.r[e*4];if(v&0x8080)return f|0x8000|e|(v&0x8000?16:0);}return f;}
 get irq(){return !!(this.connected&&this.enabled()&&!(this.r[0x40]&3)&&(this.flags()&this.r[0x40]&0xfe00));}
 read(o,s,m=false){const value=super.read(o,s,m);return !m&&o===0x44?this.flags():value;}
 write(o,s,v,m=false){const old=this.r[o]??0;super.write(o,s,v,m);if(!m&&o<32){if(this.r[o]&0x8000)this.r[o]|=old&0x800;if((old&0x8000)&&!(this.r[o]&0x8000))this.r[o]&=~0x800;}}
 word(a,v=undefined){if(a%2||a<0||a>510)throw Error('USB PMA adresse logique hors 512 octets');if(v===undefined)return this.read(a*2,2,true);this.write(a*2,2,v,true);}
 table(e,f,v=undefined){return this.word(this.r[0x50]+e*8+f,v);}
 packet(a,n,payload=undefined){if(a%2||n<0||a+n>512)throw Error('USB paquet hors PMA');if(payload!==undefined){for(let i=0;i<n;i+=2)this.word(a+i,payload[i]|(payload[i+1]??0)<<8);return;}const out=new Uint8Array(n);for(let i=0;i<n;i+=2){const v=this.word(a+i);out[i]=v&255;if(i+1<n)out[i+1]=v>>>8;}return out;}
 record(kind,e,payload,response){this.totalTokens++;this.tokens.push({kind,endpoint:e,hex:hex(payload),response});if(this.tokens.length>256)this.tokens.shift();this.lastResponse=response;return response;}
 token(kind,e=0,payload=new Uint8Array()){
  let response;if(kind==='CONNECT'){this.connected=true;response={status:'CONNECTED'};}
  else if(kind==='DISCONNECT'){this.connected=false;this.enumerated=false;response={status:'DISCONNECTED'};}
  else if(kind==='RESET'){if(!this.connected)throw Error('Hôte USB déconnecté');this.enumerated=false;this.r[0x44]|=0x400;this.r[0x4c]=0;for(let o=0;o<32;o+=4)this.r[o]&=0x8080;response={status:'RESET'};}
  else{
   if(!this.connected)throw Error('Hôte USB déconnecté');if(!Number.isInteger(e)||e<0||e>=8||!['SETUP','OUT','IN'].includes(kind))throw Error('Jeton/endpoint USB invalide');
   if(!this.enabled()||(this.r[0x40]&3)||!(this.r[0x4c]&128))response={status:'DISABLED'};
   else{
    const slots=Array.from({length:8},(_,i)=>i).filter(n=>(this.r[n*4]&15)===e&&(this.r[n*4]&0x3030));if(!slots.length)return this.record(kind,e,payload,{status:'NAK'});if(slots.length!==1)throw Error('USB adresse endpoint ambiguë');
    const slot=slots[0];let v=this.r[slot*4],type=v&0x600;if((v&0x100&&type!==0x200)||type===0x400)throw Error('USB double buffering/isochronous non porté');
    let state=kind==='IN'?(v>>>4)&3:(v>>>12)&3;if(kind==='SETUP'&&type===0x200&&state&&!(v&0x8000))state=3;
    if(state!==3)response={status:['DISABLED','STALL','NAK'][state]};
    else if(kind==='OUT'&&type===0x200&&(v&0x100)&&payload.length)response={status:'STALL'};
    else if(kind==='IN'){const count=this.table(slot,2)&0x3ff;if(count>64)throw Error('USB IN >64 octets');const data=this.packet(this.table(slot,0),count);this.r[slot*4]=((v^0x40)&~0x30)|0x20|0x80;response={status:'ACK',hex:hex(data),bytes:count};}
    else{if(kind==='SETUP'&&(payload.length!==8||type!==0x200))throw Error('USB SETUP doit faire 8 octets sur endpoint contrôle');const cfg=this.table(slot,6),blocks=(cfg>>>10)&31,capacity=cfg&0x8000?(blocks+1)*32:blocks*2;if(payload.length>64||payload.length>capacity)throw Error('USB OUT déborde le tampon configuré');this.packet(this.table(slot,4),payload.length,payload);this.table(slot,6,(cfg&0xfc00)|payload.length);v=((v^0x4000)&~0x3800)|0x2000|0x8000;if(kind==='SETUP')v=(v&~0x4030)|0x40|0x20|0x800;this.r[slot*4]=v;response={status:'ACK',bytes:payload.length};}
   }
  }
  return this.record(kind,e,payload,response);
 }
 status(){return {connected:this.connected,enumerated:this.enumerated,irq:this.irq,registers:{...this.r},totalTokens:this.totalTokens,tokens:this.tokens,lastResponse:this.lastResponse,source:'firmware-visible PMA and IRQ20',physicalUSB:false};}
}
export const hex=bytes=>Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
export function unhex(text){if(typeof text!=='string'||text.length%2||!/^([0-9a-f]{2})*$/i.test(text))throw Error('Hexadécimal invalide');return Uint8Array.from(text.match(/../g)??[],v=>parseInt(v,16));}
export function cdcConfiguration(data){
 if(data.length<9||data[0]!==9||data[1]!==2||(data[2]|data[3]<<8)!==data.length)throw Error('Descripteur de configuration USB invalide');let at=0,current=null,union=null;const interfaces=new Map();
 while(at<data.length){const n=data[at];if(n<2||at+n>data.length)throw Error('Descripteur USB tronqué');const d=data.slice(at,at+n),k=d[1];if(k===4&&n>=9){current=`${d[2]}:${d[3]}`;interfaces.set(current,{n:d[2],alt:d[3],cls:d[5],sub:d[6],endpoints:[]});}else if(k===5&&n>=7&&current)interfaces.get(current).endpoints.push([d[2],d[3]&3,(d[4]|d[5]<<8)&2047]);else if(k===0x24&&n>=5&&d[2]===6)union=[d[3],d[4]];at+=n;}
 const controls=[...interfaces.values()].filter(d=>!d.alt&&d.cls===2&&d.sub===2);if(controls.length!==1)throw Error('Une fonction CDC ACM requise');const control=controls[0];const choices=[...interfaces.values()].filter(d=>!d.alt&&d.cls===10&&(!union||union[0]===control.n&&union[1]===d.n));if(choices.length!==1)throw Error('Interface CDC data absente/ambiguë');const d=choices[0],bulk=d.endpoints.filter(e=>e[1]===2),rx=bulk.filter(e=>e[0]&128),tx=bulk.filter(e=>!(e[0]&128));if(rx.length!==1||tx.length!==1||bulk.some(e=>e[2]<1||e[2]>64))throw Error('Endpoints CDC non supportés');return {configuration:data[5],controlInterface:control.n,dataInterface:d.n,bulkIn:rx[0][0],bulkOut:tx[0][0],inSize:rx[0][2],outSize:tx[0][2]};
}
export class CdcHost{
 constructor(usb){this.usb=usb;this.epoch=0;this.state='disconnected';this.error=null;this.control=null;this.layout=null;this.outgoing=[];this.received=[];this.sentTotal=0;this.receivedTotal=0;this.events=[];this.time=0;this.next=Infinity;this.ep0Size=8;this.phase=0;this.deviceDescriptor=new Uint8Array();this.configurationDescriptor=new Uint8Array();}
 deviceReset(usb,time){this.usb=usb;this.usb.token('CONNECT');this.epoch++;this.state='waiting_device';this.error=null;this.control=null;this.layout=null;this.outgoing=[];this.received=[];this.sentTotal=0;this.receivedTotal=0;this.ep0Size=8;this.phase=0;this.time=time;this.next=time+2048;this.record('device_reset',{epoch:this.epoch});}
 record(kind,values={}){this.events.push({time:this.time,kind,...values});if(this.events.length>256)this.events.shift();}
 start(time){this.time=time;this.usb.token('CONNECT');this.usb.token('RESET');this.state='enumerating';this.error=null;this.next=time+1;this.request('device8',0x80,6,0x100,0,8);}
 close(){this.usb.token('DISCONNECT');this.state='disconnected';this.control=null;this.outgoing=[];this.next=Infinity;}
 request(name,kind,request,value,index,length,payload=new Uint8Array()){if(this.next===Infinity)this.next=this.time+1;const setup=new Uint8Array([kind,request,value&255,value>>>8,index&255,index>>>8,length&255,length>>>8]);this.control={name,setup,directionIn:!!(kind&128),length,payload,position:0,data:[],stage:'setup'};this.deadline=this.time+3600000000;this.record('control_request',{name,setup:hex(setup)});}
 queue(data){if(this.state!=='ready')throw Error('USB CDC non prêt');if(!data.length||data.length+this.outgoing.length>65536)throw Error('File CDC pleine ou paquet vide');this.outgoing.push(...data);if(this.next===Infinity)this.next=this.time+1;}
 token(k,e=0,p=new Uint8Array()){const r=this.usb.token(k,e,p);if(r.status==='STALL')throw Error('USB STALL pendant '+k+' endpoint '+e);return r;}
 tick(time){this.time=time;if(['disconnected','error'].includes(this.state)||time<this.next)return;this.next=time+2048;try{if(this.state==='waiting_device'){if(this.usb.enabled()&&!(this.usb.r[0x40]&3))this.start(time);return;}if(this.control){if(time>this.deadline)throw Error('USB timeout virtuel '+this.control.name+'/'+this.control.stage);this.controlTick();return;}if(this.state!=='ready')return;this.phase^=1;if(this.outgoing.length&&this.phase){const data=new Uint8Array(this.outgoing.slice(0,this.layout.outSize));if(this.token('OUT',this.layout.bulkOut&15,data).status==='ACK'){this.outgoing.splice(0,data.length);this.sentTotal+=data.length;this.record('bulk_OUT',{hex:hex(data)});}}else{const r=this.token('IN',this.layout.bulkIn&15);if(r.status==='ACK'){const data=unhex(r.hex);this.received.push(...data);this.receivedTotal+=data.length;if(this.received.length>65536)this.received.splice(0,this.received.length-65536);this.record('bulk_IN',{hex:r.hex});}}}catch(e){this.error=e.message;this.state='error';this.control=null;this.next=Infinity;this.record('error',{message:e.message});}}
 controlTick(){const c=this.control;if(c.stage==='setup'){if(this.token('SETUP',0,c.setup).status==='ACK')c.stage=c.length?(c.directionIn?'in':'out'):'status_in';}
 else if(c.stage==='in'){const r=this.token('IN');if(r.status!=='ACK')return;const data=unhex(r.hex);c.data.push(...data);if(c.data.length>c.length)throw Error('USB réponse trop longue');if(data.length<this.ep0Size||c.data.length===c.length)c.stage='status_out';}
 else if(c.stage==='out'){const data=c.payload.slice(c.position,c.position+this.ep0Size);if(this.token('OUT',0,data).status==='ACK'){c.position+=data.length;if(c.position===c.length)c.stage='status_in';}}
 else if(c.stage==='status_out'){if(this.token('OUT').status==='ACK')this.complete();}
 else if(c.stage==='status_in'){const r=this.token('IN');if(r.status==='ACK'){if(r.bytes)throw Error('USB status non vide');this.complete();}}}
 complete(){const c=this.control,name=c.name,data=new Uint8Array(c.data);this.control=null;this.record('control_complete',{name,hex:hex(data)});
 if(name==='device8'){if(data.length!==8||data[0]!==18||data[1]!==1||![8,16,32,64].includes(data[7]))throw Error('Descripteur device8 invalide');this.ep0Size=data[7];this.request('address',0,5,1,0,0);}
 else if(name==='address')this.request('device',0x80,6,0x100,0,18);
 else if(name==='device'){if(data.length!==18||data[0]!==18||data[1]!==1)throw Error('Descripteur device invalide');this.deviceDescriptor=data;this.request('config9',0x80,6,0x200,0,9);}
 else if(name==='config9'){if(data.length!==9||data[0]!==9||data[1]!==2)throw Error('Descripteur config9 invalide');const len=data[2]|data[3]<<8;if(len<9||len>4096)throw Error('Taille configuration invalide');this.request('configuration',0x80,6,0x200,0,len);}
 else if(name==='configuration'){this.configurationDescriptor=data;this.layout=cdcConfiguration(data);this.request('configure',0,9,this.layout.configuration,0,0);}
 else if(name==='configure')this.request('line_coding',0x21,0x20,0,this.layout.controlInterface,7,new Uint8Array([0,0xc2,1,0,0,0,8]));
 else if(name==='line_coding')this.request('control_lines',0x21,0x22,3,this.layout.controlInterface,0);
 else if(name==='control_lines'){this.state='ready';this.usb.enumerated=true;this.record('ready',{layout:this.layout});}}
 readSince(cursor){const base=this.receivedTotal-this.received.length;if(cursor<base||cursor>this.receivedTotal)throw Error('Curseur CDC hors tampon');return new Uint8Array(this.received.slice(cursor-base));}
 status(){return {state:this.state,epoch:this.epoch,error:this.error,layout:this.layout,transfer:this.control?this.control.name+'/'+this.control.stage:null,deviceDescriptor:hex(this.deviceDescriptor),configurationDescriptor:hex(this.configurationDescriptor),queuedBytes:this.outgoing.length,sentTotal:this.sentTotal,receivedTotal:this.receivedTotal,receivedBase:this.receivedTotal-this.received.length,receivedHex:hex(this.received),events:this.events,source:'executed firmware PMA only',physicalSerialBridge:false};}
}
