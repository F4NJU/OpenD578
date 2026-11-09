/* CPS host workflow. Its sole device interface is CpsClient + the CDC connection epoch.
 * It never receives an MCU, SRAM, LCD or NAND object. */
import {SHA256} from './sha256.mjs?build=web0151r2';
import {unhex} from './usb-device.mjs?build=web0151r2';
const BASE=0x800000,SIZE=131072,NAME=35,NAME_SIZE=16;
const digest=b=>new SHA256().update(b).hex();
export class CpsMemory {
 constructor(client){this.client=client;this.state='idle';this.error=null;this.original=null;this.expected=null;this.evidence=null;this.events=[];this.evidenceHistory=[];this.restoring=false;}
 get active(){return ['backup','writing','waiting_reset','restarting','verifying'].includes(this.state);}
 record(event,time){this.events.push({event,time,epoch:this.client.cdc.epoch??0});if(this.events.length>32)this.events.shift();}
 rename(name,time=0){
   if(this.state!=='idle')throw Error('Restaurer la sauvegarde avant une autre modification de cette session');
   if(typeof name!=='string'||!name.length||name.length>NAME_SIZE||!/^[ -~]+$/.test(name))throw Error('Nom : 1 à 16 caractères ASCII imprimables');
   this.client.startRead(BASE,SIZE,time);this.name=name;this.state='backup';this.error=null;this.record('backup_start',time);
 }
 block(){const blocks=this.client.blocks;if(blocks.length!==SIZE/16||blocks.some((b,i)=>b.address!==BASE+i*16))throw Error('Sauvegarde CPS incomplète ou désordonnée');const data=new Uint8Array(SIZE);for(let i=0;i<blocks.length;i++)data.set(unhex(blocks[i].hex),i*16);return data;}
 commit(data,time){this.epoch=this.client.cdc.epoch??0;this.client.startBlockCommit(BASE,data,time);this.state='writing';this.record(this.restoring?'restore_write_start':'write_start',time);}
 verify(time=0){if(this.state!=='awaiting_verification'||this.client.cdc.state!=='ready')throw Error('Attendre le redémarrage et la réénumération USB');this.client.startRead(BASE,SIZE,time);this.state='verifying';this.record('readback_start',time);}
 restore(time=0){if(this.state!=='verified'||!this.original)throw Error('Une modification vérifiée est nécessaire avant restauration');this.restoring=true;this.expected=this.original.slice();this.commit(this.expected,time);this.evidence=null;}
 tick(time){try{
   if(!this.active)return;
   if(this.client.state==='error')throw Error(this.client.error);
   if(this.client.cdc.state==='disconnected'||this.client.cdc.state==='error')throw Error('Connexion CPS interrompue ; conserver la sauvegarde et le diagnostic');
   if(this.state==='backup'&&this.client.state==='complete'){
     this.original=this.block();this.expected=this.original.slice();this.expected.fill(0,NAME,NAME+NAME_SIZE);this.expected.set(new TextEncoder().encode(this.name),NAME);this.before=digest(this.original);this.commit(this.expected,time);
   }else if(this.state==='writing'&&this.client.state==='complete'){this.state='waiting_reset';this.record('END_ACK_not_validation',time);}
   if(['writing','waiting_reset'].includes(this.state)&&(this.client.cdc.epoch??0)>this.epoch){this.state='restarting';this.record('USB_device_reset',time);}
   if(this.state==='restarting'&&this.client.cdc.state==='ready'){this.state='awaiting_verification';this.record('USB_reenumerated',time);}
   if(this.state==='verifying'&&this.client.state==='complete'){
     const actual=this.block();let differences=0,firstDifference=null,preserved=0;
     for(let i=0;i<SIZE;i++){if(actual[i]!==this.expected[i]){differences++;firstDifference??=i;}if((i<NAME||i>=NAME+NAME_SIZE)&&actual[i]===this.original[i])preserved++;}
     this.evidence={address:BASE,length:SIZE,beforeSha256:this.before,expectedSha256:digest(this.expected),actualSha256:digest(actual),differences,firstDifference,preservedBytesOutsideName:preserved,requiredPreservedBytes:SIZE-NAME_SIZE,afterReset:(this.client.cdc.epoch??0)>this.epoch,restoration:this.restoring};
     if(differences)throw Error('Relecture CPS différente après redémarrage : '+differences+' octet(s), premier décalage '+firstDifference);
     this.evidenceHistory.push({...this.evidence});this.state=this.restoring?'restored':'verified';this.record(this.restoring?'restore_verified':'write_verified',time);
   }
 }catch(e){this.error=e.message;this.state='error';this.record('error',time);}}
 backup(){if(!this.original)throw Error('Sauvegarde CPS indisponible');return this.original.slice();}
 status(){return {state:this.state,error:this.error,name:this.name??null,restoring:this.restoring,backupAvailable:!!this.original,evidence:this.evidence,evidenceHistory:this.evidenceHistory,events:this.events,progress:{remaining:this.client.jobs.length+(this.client.pending?1:0),total:this.client.totalJobs??0},scope:'Channel 1 name, OEM V1.21 GD32; 128 KiB read-modify-write; journal trailer owned by OEM; no direct memory access',verified:['verified','restored'].includes(this.state)};}
}
