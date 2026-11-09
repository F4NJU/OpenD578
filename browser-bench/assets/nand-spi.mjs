/* Toshiba TC58CVG1S3H compatible NAND GPIO-serial bus (captured reads and
 * isolated copy-on-write). Port of OpenD578 V11.8 emulate_nand_v121.py.
 * Copyright 2026 OpenD578 contributors; GPL-3.0-or-later.
 */
import {NAND_PAGES,NAND_PAGE,NAND_OOB_PAGE,NAND_PAGES_PER_BLOCK} from './nand.mjs';
const ALLOWED=new Set([0x9f,0x0f,0x13,0x03,0x0b,0x3b,0x1f,0x06,0x04,0xff,0xfe,0x02,0x84,0x10,0xd8,0x2a]);
export class NandSpi {
  constructor(storage,{idle=1,busyPolls=1,onRead=null}={}) {this.storage=storage;this.idle=idle&1;this.busyPolls=busyPolls;this.onRead=onRead;this.reset();}
  reset(){this.features=new Map([[0xa0,0x38],[0xb0,0x16]]);this.status=0;this.pendingBusy=0;this.cachedPage=null;this.cache=null;
    this.cs=1;this.clk=0;this.mosi=0;this.miso=this.idle;this.io0=this.idle;
    this.accumulator=0;this.inputBits=0;this.inputBytes=[];this.outputs=new Map();this.transactions=0;this.pages=new Map();
    this.opcodes=new Map();this.readBytes=0;this.programBuffer=null;this.lastCommand=null;this.writes=0;this.erases=0;
  }
  begin(){this.inputBits=0;this.accumulator=0;this.inputBytes=[];this.outputs.clear();this.miso=this.idle;this.io0=this.idle;}
  feature(address){
    if(address===0xc0){let v=this.status;if(this.pendingBusy>0){v|=1;this.pendingBusy--;}return v;}
    if(!this.features.has(address))throw new Error(`NAND feature non identifiee 0x${address.toString(16)}`);
    return this.features.get(address);
  }
  outputByte(byteIndex){
    if(this.outputs.has(byteIndex))return this.outputs.get(byteIndex);
    let result=this.idle?0xff:0,cmd=this.inputBytes[0];
    if(cmd===0x9f&&byteIndex>=2){const pos=byteIndex-2;if(pos>1)throw new Error('NAND ID hors zone connue');result=[0x98,0xcb][pos];}
    else if(cmd===0x0f&&byteIndex>=2)result=this.feature(this.inputBytes[1]);
    else if([0x03,0x0b,0x3b].includes(cmd)&&byteIndex>=4){
      if(!this.cache)throw new Error('NAND lecture cache sans 0x13 precedent');
      const column=(((this.inputBytes[1]<<8)|this.inputBytes[2])&0xfff),offset=column+byteIndex-4;
      if(offset>=this.cache.length)throw new Error(`NAND colonne 0x${offset.toString(16)} hors page`);
      result=this.cache[offset];this.readBytes++;
      if(this.onRead){const main=offset<NAND_PAGE;this.onRead({zone:main?'main':'oob',page:this.cachedPage,column:main?offset:offset-NAND_PAGE,address:this.cachedPage*(main?NAND_PAGE:NAND_OOB_PAGE)+(main?offset:offset-NAND_PAGE),value:result,source:this.cacheSources[main?'main':'oob']});}
    }
    this.outputs.set(byteIndex,result);return result;
  }
  end(){const d=this.inputBytes;if(!d.length)return;
    const cmd=d[0];this.lastCommand=cmd;this.opcodes.set(cmd,(this.opcodes.get(cmd)??0)+1);this.transactions++;
    if(cmd===0x13){
      if(d.length!==4)throw new Error('NAND 0x13 exige ligne 3 octets');
      const row=((d[1]<<16)|(d[2]<<8)|d[3])>>>0;
      if(row>=NAND_PAGES)throw new Error('NAND page hors capture');
      if(!(this.features.get(0xb0)&0x10)||(this.features.get(0xb0)&0x40))throw new Error('NAND ECC OFF / mode special non capture');
      const mainEntry=this.storage.readPageSync('main',row),oobEntry=this.storage.readPageSync('oob',row),main=mainEntry.bytes,oob=oobEntry.bytes;
      this.cacheSources={main:mainEntry.source,oob:oobEntry.source};
      this.cache=new Uint8Array(NAND_PAGE+NAND_OOB_PAGE);this.cache.set(main);this.cache.set(oob,NAND_PAGE);
      const ecc=this.storage.readPageSync('ecc',row).bytes[0];this.status=(ecc|(this.status&2))&0xff;
      this.pendingBusy=this.busyPolls;this.cachedPage=row;this.pages.set(row,(this.pages.get(row)??0)+1);
    }else if(cmd===0x1f){
      if(d.length!==3)throw new Error('NAND Set Feature exige 3 octets');
      if(d[1]===0xa0)this.features.set(0xa0,d[2]&0xb8);
      else if(d[1]===0xb0)this.features.set(0xb0,(d[2]&0xd2)|4);
      else throw new Error(`NAND feature ecriture non documentee 0x${d[1].toString(16)}`);
    }else if(cmd===0x06)this.status|=2;
    else if(cmd===0x04)this.status&=~2;
    else if(cmd===0xff||cmd===0xfe){this.status=0;this.pendingBusy=this.busyPolls;this.cachedPage=null;this.cache=null;this.programBuffer=null;}
    else if(cmd===0x02||cmd===0x84){
      if(d.length<4)throw new Error('NAND Program Load sans donnees');
      const col=(d[1]<<8)|d[2];if(col+d.length-3>2112)throw new Error('NAND Program Load hors page');
      if(cmd===0x02)this.programBuffer=new Uint8Array(2112).fill(0xff);
      if(!this.programBuffer)throw new Error('NAND random load sans buffer');
      this.programBuffer.set(d.slice(3),col);
    }else if(cmd===0x10||cmd===0xd8){
      if(d.length!==4)throw new Error('NAND commande operation ligne incomplete');
      const row=((d[1]<<16)|(d[2]<<8)|d[3])>>>0;
      if(row>=NAND_PAGES)throw new Error('NAND row hors appareil');
      if(!(this.status&2))throw new Error('NAND ecriture sans WEL');
      if(this.features.get(0xa0)&0x38)throw new Error('NAND blocs proteges');
      if(cmd===0xd8){this.storage.eraseSync(row>>>6);this.erases++;}
      else {
        if(!this.programBuffer)throw new Error('NAND execute sans buffer');
        this.storage.programSync('main',row,0,this.programBuffer.slice(0,2048));
        this.storage.programSync('oob',row,0,this.programBuffer.slice(2048));
        this.programBuffer=null;this.writes++;
      }
      this.status=0;this.pendingBusy=this.busyPolls;
    }else if(![0x9f,0x0f,0x03,0x0b,0x3b,0x2a].includes(cmd))throw new Error(`NAND opcode non modele 0x${cmd.toString(16)}`);
  }
  // GPIOB: PB8 CS#, PB15 CLK, PB14 IO0/MOSI. GPIOA PA15 MISO.
  drive(levels,writeMask){
    const cs=Number(Boolean(levels&(1<<8))),clk=Number(Boolean(levels&(1<<15))),mosi=Number(Boolean(levels&(1<<14)));
    if((writeMask&(1<<8))&&cs!==this.cs){this.cs=cs;if(cs)this.end();else this.begin();}
    if(writeMask&(1<<14))this.mosi=mosi;
    if((writeMask&(1<<15))&&clk!==this.clk){
      if(!this.cs){
        if(!clk){
          if(this.inputBytes[0]===0x3b&&this.inputBits>=32){
            const bitOffset=(this.inputBits-32)*2,index=4+(bitOffset>>>3),shift=bitOffset&7;
            const value=this.outputByte(index);this.miso=(value>>>(7-shift))&1;this.io0=(value>>>(6-shift))&1;
          }else{const idx=this.inputBits>>>3,shift=this.inputBits&7;this.miso=(this.outputByte(idx)>>>(7-shift))&1;}
        }else{
          this.accumulator=(this.accumulator<<1)|this.mosi;this.inputBits++;
          if(!(this.inputBits&7)){
            this.inputBytes.push(this.accumulator&255);this.accumulator=0;
            if(this.inputBytes.length===1&&!ALLOWED.has(this.inputBytes[0]))throw new Error(`NAND commande 0x${this.inputBytes[0].toString(16)} non supportee`);
          }
        }
      }
      this.clk=clk;
    }
  }
  summary(){return {pages:Object.fromEntries(this.pages),lastCommand:this.lastCommand,transactions:this.transactions,readBytes:this.readBytes,cachedPage:this.cachedPage,
    miso:this.miso,opcodes:Object.fromEntries(this.opcodes),writes:this.writes,erases:this.erases};}
}
