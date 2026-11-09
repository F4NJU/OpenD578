/* Cortex-M4 CPU backend: actual Unicorn ARM/T32 WASM, never Thumb16 interpreter.
 * Peripheral reads/writes are dispatched by physical MMIO address.
 * GPL-3.0-or-later, OpenD578 project. Upstream Unicorn.js GPL-2.0:
 * licensing compatibility must be reviewed before distributing its binary.
 */
import {BoardRuntime} from './board-runtime.mjs?build=web0151r5';
import {FLASH_START,FLASH_SIZE,SRAM_START,SRAM_SIZE,checkVector,hex} from './memory.mjs?build=web0151r5';
import {BoardIO,GPIO_BASE,ADC0,USART0,USART1} from './board-io.mjs?build=web0151r5';
import {BootPeripherals, RCU_BASE, FMC_BASE, SCB_BASE, BITBAND_RCU} from './startup-peripherals.mjs?build=web0151r5';
export const CORE_REVISION='web0151r5';
export function ownsSystemMmio(a){return (a>=RCU_BASE&&a<RCU_BASE+0x1000)||(a>=FMC_BASE&&a<FMC_BASE+0x1000)||(a>=SCB_BASE&&a<SCB_BASE+0x1000)||(a>=BITBAND_RCU&&a<BITBAND_RCU+0x1000);}
const toArray=(value)=>value instanceof Uint8Array?value:new Uint8Array(value);
function bytesOf(value,size){const out=new Uint8Array(size);for(let i=0;i<size;i++)out[i]=(value>>>(8*i))&255;return out;}
export class UnicornCortexM4 {
  constructor(lib,{board=null,debug=false}={}){
    if(!lib?.Unicorn||lib.ARCH_ARM===undefined||lib.ARM_REG_PC===undefined)throw new Error('Unicorn WASM ARM incompatible');
    this.lib=lib;this.board=board??new BoardIO();this.debug=debug;this.debugHooks=[];this.instructionCount=null;this.debugHook=null;this.runs=0;this.lastBudget=0;this.stop=null;this.lastFault=null;this.lastPc=0;this.started=false;this.trace=[];this.modelError=null;this.boot=new BootPeripherals();this.cpuModelName='default_MCLASS';this.coreRevision=CORE_REVISION;
    const mode=(lib.MODE_THUMB??16)|(lib.MODE_MCLASS??32);
    this.uc=new lib.Unicorn(lib.ARCH_ARM,mode);
    // The native V11.8 explicitly selects Cortex-M4 (ID 9). MCLASS mode
    // alone does not guarantee the correct ARMv7E-M instruction set.
    const cortexM4=lib.CPU_ARM_CORTEX_M4;
    if(cortexM4===undefined||typeof this.uc.ctl_set_cpu_model!=='function'||typeof this.uc.ctl_get_cpu_model!=='function'){
      this.uc.close?.();throw new Error('Runtime WASM incompatible : sélection et lecture du modèle Cortex-M4 requises.');
    }
    this.uc.ctl_set_cpu_model(cortexM4);
    this.cpuModelId=this.uc.ctl_get_cpu_model();
    if(this.cpuModelId!==cortexM4){this.uc.close?.();throw new Error('Le moteur a ignoré le modèle Cortex-M4 demandé.');}
    this.cpuModelName='Cortex-M4 (sélection relue et vérifiée)';
    this._map(FLASH_START,FLASH_SIZE);this._map(SRAM_START,SRAM_SIZE);
    this._map(0x00000000,FLASH_SIZE); // Cortex-M boot flash alias
    this._map(0x40000000,0x00040000); // GD32 peripheral bus (partial)
    this._map(0xe000e000,0x00001000); // SCB, SysTick, NVIC register windows
    this._map(BITBAND_RCU,0x1000); // RCU peripheral bit-band alias
    this.flash=new Uint8Array(FLASH_SIZE);this.flash.fill(255);
    this.time=0;this.corePending=new Set();this.irqActive=false;this.irqLog=[];this.hardware=new BoardRuntime(this);
    this._map(0x420d8000,0x1000);this._map(0x420e0000,0x1000);
    this._installPeripheralHooks();
    this._installExecutionBoundaries();
    if(this.debug)this.setDebug(true);
  }
  _map(a,size){this.uc.mem_map(a,size,this.lib.PROT_ALL??7);}
  _write(a,bytes){this.uc.mem_write(a,toArray(bytes));}
  _get(r){return this.uc.reg_read_i32(r)>>>0;}
  _set(r,v){this.uc.reg_write_i32(r,v>>>0);}
  _installPeripheralHooks(){
    if(typeof this.uc.hook_add!=='function')throw new Error('Unicorn ARM WASM: hook_add non disponible');
    const WRITE=this.lib.HOOK_MEM_WRITE,READ=this.lib.HOOK_MEM_READ;
    if(WRITE===undefined||READ===undefined)throw new Error('Unicorn ARM WASM: hooks MMIO absents');
    const normalize=args=>{
      let a=Array.from(args);
      if(a.length>=5&&typeof a[0]==='object')a=a.slice(1);
      return {type:Number(a[0]),address:Number(a[1])>>>0,size:Number(a[2]),value:Number(a[3])>>>0};
    };
    const peripheral=a=>a>=0x40000000&&a<0x40040000;
    const invoke=(write,address,size,value=0)=>{
      try{
        return this.hardware.access(address,size,write,value);
        throw new Error('Adresse peripherique hors plage modelisee');
      }catch(error){
        this.modelError={address,size,write,reason:String(error?.message??error)};
        this.uc.emu_stop?.();
        return write?null:0;
      }
    };
    // Unicorn.js builds may deliver callbacks for a wider range than
    // requested. Never treat ordinary Flash, SRAM or boot alias accesses as
    // MMIO. The CPU itself reads these already-mapped memory regions.
    const isMmioAddress=address=>ownsSystemMmio(address)||peripheral(address)||(address>=0x420d8000&&address<0x420d9000)||(address>=0x420e0000&&address<0x420e1000);
    const readCb=(...args)=>{
      const {address,size}=normalize(args);
      if(!isMmioAddress(address))return;
      const value=invoke(false,address,size);
      if(!this.modelError&&size>=1&&size<=4)this.uc.mem_write(address,bytesOf(value,size));
    };
    const writeCb=(...args)=>{
      const {address,size,value}=normalize(args);
      if(!isMmioAddress(address))return;
      invoke(true,address,size,value);
    };
    // Unicorn.js ABI: hook_add(type, callback, user_data, begin, end, extra).
    // Keep all memory observers restricted to the physical MMIO windows.
    for(const [start,end] of [[0x40000000,0x4003ffff],[BITBAND_RCU,BITBAND_RCU+0xfff],[SCB_BASE,SCB_BASE+0xfff],[0x420d8000,0x420d8fff],[0x420e0000,0x420e0fff]]){
      this.uc.hook_add(WRITE,writeCb,null,start,end);this.uc.hook_add(READ,readCb,null,start,end);
    }
    if(this.lib.HOOK_MEM_INVALID!==undefined)this.uc.hook_add(this.lib.HOOK_MEM_INVALID,(...args)=>{
      const {type,address,size,value}=normalize(args);
      this.lastFault={type,address,size,value};return false;
    },null,1,0);
  }
  _installExecutionBoundaries(){
    this.uc.hook_add(this.lib.HOOK_INTR,(_uc,number)=>{
      if(number===8&&this.irqActive){this.internalStop='exception-return';this.uc.emu_stop();}
      else {this.modelError={reason:'CPU exception '+number,address:this._get(this.lib.ARM_REG_PC)};this.uc.emu_stop();}
    },null,1,0);
    this.uc.hook_add(this.lib.HOOK_MEM_WRITE,(_uc,type,address,size,value)=>{
      const a=Number(address)>>>0;if(a<0x082f5000||a>=0x08300000)return;
      try{this.hardware.fmc.program(a,size,Number(value)>>>0);}catch(e){this.modelError={reason:e.message,address:a};this.uc.emu_stop();}
    },null,0x082f5000,0x082fffff);
    this.sleepHook=this.uc.hook_add(this.lib.HOOK_CODE,(_engine,address)=>{
      const pc=Number(address)>>>0;
      try{
        this.hardware.steps++;this.hardware.advance(1);
        if(this.resetRequest){this.internalStop='system-reset';this.uc.emu_stop();return;}
        if(!this.irqActive&&(this.corePending.size||((this.boot.nvicPending[0]&this.boot.nvicEnable[0])||(this.boot.nvicPending[1]&this.boot.nvicEnable[1])||(this.boot.nvicPending[2]&this.boot.nvicEnable[2])))){
          const e=this.hardware.selectedInterrupt();if(e!==null){this.internalStop={exception:e};this.uc.emu_stop();return;}
        }
        let offset=pc>=FLASH_START&&pc<FLASH_START+FLASH_SIZE?pc-FLASH_START:pc<FLASH_SIZE?pc:-1;
        let opcode;if(offset>=0)opcode=this.flash[offset]|(this.flash[offset+1]<<8);else{const b=this.uc.mem_read(pc,2);opcode=b[0]|b[1]<<8;}
        if(opcode===0xbf40)this.eventRegister=true;
        if(opcode===0xbf30||opcode===0xbf20){
          if(opcode===0xbf20&&this.eventRegister){this.eventRegister=false;return;}
          this.sleeping=true;this._set(this.lib.ARM_REG_PC,(pc+2)|1);this.internalStop='sleep';this.uc.emu_stop();
        }
      }catch(e){this.modelError={reason:e.message,address:pc};this.uc.emu_stop();}
    },null,1,0);
  }
  enterException(exception){
    const L=this.lib,get=r=>this._get(r),set=(r,v)=>this._set(r,v),sp=get(L.ARM_REG_SP),psp=!!(get(L.ARM_REG_CONTROL)&2),pad=sp&7,frame=sp-32-pad;
    if(this.irqActive||pad!==0&&pad!==4||frame<SRAM_START||frame+32>SRAM_START+SRAM_SIZE)throw Error('Exception frame non pris en charge');
    const regs=[L.ARM_REG_R0,L.ARM_REG_R1,L.ARM_REG_R2,L.ARM_REG_R3,L.ARM_REG_R12,L.ARM_REG_LR,L.ARM_REG_PC,L.ARM_REG_XPSR],values=regs.map(get);values[7]=((values[7]&~512)|(pad?512:0))>>>0;
    const vector=this.boot.scb.get(0xd08)+4*exception,bytes=this.uc.mem_read(vector,4),handler=(bytes[0]|bytes[1]<<8|bytes[2]<<16|bytes[3]<<24)>>>0;
    if(!(handler&1)||!((handler>=FLASH_START&&handler<FLASH_START+FLASH_SIZE)||(handler<FLASH_SIZE)||(handler>=SRAM_START&&handler<SRAM_START+SRAM_SIZE)))throw Error('Vecteur exception invalide '+exception);
    const fb=new Uint8Array(32),dv=new DataView(fb.buffer);values.forEach((v,i)=>dv.setUint32(i*4,v,true));this.uc.mem_write(frame,fb);
    set(psp?L.ARM_REG_PSP:L.ARM_REG_MSP,frame);const handlerSp=get(L.ARM_REG_MSP);set(L.ARM_REG_XPSR,(values[7]&0xf8000000)|0x01000000|exception);set(L.ARM_REG_SP,handlerSp);set(L.ARM_REG_LR,psp?0xfffffffd:0xfffffff9);set(L.ARM_REG_PC,handler);
    this.irqActive=true;this.corePending.delete(exception);if(exception>=16)this.boot.nvicPending[(exception-16)>>>5]&=~(1<<((exception-16)&31));
    this.irqContext={exception,frame,values,regs,handlerSp,entry:this.hardware.steps,callee:Array.from({length:8},(_,i)=>get(L['ARM_REG_R'+(i+4)]))};
    this.irqLog.push({step:this.hardware.steps,exception,handler,frame,interruptedPc:values[6]});if(this.irqLog.length>2048)this.irqLog.shift();
  }
  exitException(){
    const L=this.lib,c=this.irqContext;let target=(this._get(L.ARM_REG_PC)|1)>>>0;if(![0xfffffff9,0xfffffffd].includes(target))target=this._get(L.ARM_REG_LR);
    if(![0xfffffff9,0xfffffffd].includes(target))throw Error('EXC_RETURN non pris en charge '+target.toString(16));
    if(this._get(L.ARM_REG_MSP)!==c.handlerSp)throw Error('MSP Handler déséquilibré');const usePsp=target===0xfffffffd,sr=usePsp?L.ARM_REG_PSP:L.ARM_REG_MSP,frame=this._get(sr);
    if(frame<SRAM_START||frame+32>SRAM_START+SRAM_SIZE)throw Error('Exception return frame hors SRAM');const bytes=toArray(this.uc.mem_read(frame,32)),dv=new DataView(bytes.buffer,bytes.byteOffset,32),values=Array.from({length:8},(_,i)=>dv.getUint32(i*4,true));
    if(!(values[7]&0x01000000)||(values[7]&511))throw Error('Exception retour autre que Thread Thumb');
    if(c.exception!==14&&(frame!==c.frame||values.some((v,i)=>v!==c.values[i])||c.callee.some((v,i)=>v!==this._get(L['ARM_REG_R'+(i+4)]))))throw Error('Contexte modifié hors PendSV');
    this._set(L.ARM_REG_XPSR,values[7]&~512);this._set(L.ARM_REG_CONTROL,(this._get(L.ARM_REG_CONTROL)&~2)|(usePsp?2:0));this._set(sr,frame+32+(values[7]&512?4:0));for(let i=0;i<7;i++)this._set(c.regs[i],i===6?values[i]|1:values[i]);
    this.irqLog.at(-1).returned=true;this.irqActive=false;this.irqContext=null;
  }
  loadFlash(bytes){if(!(bytes instanceof Uint8Array)||bytes.length!==FLASH_SIZE)throw new Error('Flash 3 Mio requise');
    this.flash.set(bytes);this._write(FLASH_START,bytes);this._write(0,bytes);
    this.sctBoot=bytes.slice(0xf56cc,0xf56cc+2048);
  }
  requestReset(source){if(!this.resetRequest)this.resetRequest={source,time:this.time,step:this.hardware.steps};this.uc.emu_stop?.();}
  reset(vector=FLASH_START,{system=false,cause=null}={}){
    const vectors=checkVector(this.flash.subarray(vector-FLASH_START,vector-FLASH_START+8),vector);
    if(!vectors.ok)throw new Error('Vecteurs de reset invalides : '+vectors.issues.join('; '));
    const retained=system?{time:this.time,steps:this.hardware.steps,rtc:this.hardware.rtc,gps:this.hardware.gps,gpsWire:this.hardware.serial.get(0x40004400).device.wire.map(v=>v.slice()),micWire:this.hardware.serial.get(0x40013800).device.wire.map(v=>v.slice()),rfInputs:new Map(this.hardware.rf.externalInputs),inputs:{keyMinimum:new Map(this.hardware.keyMinimum),keyRelease:new Map(this.hardware.keyRelease),powerReleaseAt:this.hardware.powerReleaseAt,encoderEvents:this.hardware.encoderEvents.map(e=>({...e})),encoderTail:this.hardware.encoderTail},bdctl:this.boot.clock.get(32),flags:this.boot.clock.get(36),cdc:this.hardware.cdc,cps:this.hardware.cps,cpsEdit:this.hardware.cpsEdit}:null;
    if(!system)this._write(SRAM_START,new Uint8Array(SRAM_SIZE).fill(0xa5));
    this.board.reset({preserveInputs:true,preserveExternal:system});this.boot.reset(vector);this.time=retained?.time??0;this.corePending.clear();this.irqActive=false;this.irqContext=null;this.irqLog=[];this.sleeping=false;this.eventRegister=false;this.resetRequest=null;this.hardware.reset();
    if(retained){this.hardware.steps=retained.steps;this.boot.clock.set(32,retained.bdctl);this.boot.clock.set(36,((retained.flags&0xfc000000)|(cause==='watchdog'?1<<29:1<<28))>>>0);this.hardware.rtc=retained.rtc;this.hardware.rtc.boot=this.boot;this.hardware.rtc.pmu=0;this.hardware.gps=retained.gps;this.hardware.serial.get(0x40004400).device.wire=retained.gpsWire;this.hardware.serial.get(0x40013800).device.wire=retained.micWire;this.hardware.rf.externalInputs=retained.rfInputs;Object.assign(this.hardware,retained.inputs);
      if(retained.cdc.state!=='disconnected'){retained.cdc.deviceReset(this.hardware.usb,this.time);retained.cps.deviceReset?.();this.hardware.cdc=retained.cdc;this.hardware.cps=retained.cps;this.hardware.cpsEdit=retained.cpsEdit;}
      this.resetEvents??=[];this.resetEvents.push({source:cause,time:this.time,step:retained.steps,vector});if(this.resetEvents.length>32)this.resetEvents.shift();this.resetGeneration=(this.resetGeneration??0)+1;
    }else{this.resetEvents=[];this.resetGeneration=0;}
    this._set(this.lib.ARM_REG_XPSR,0x01000000);
    this._set(this.lib.ARM_REG_CONTROL,0);this._set(this.lib.ARM_REG_PRIMASK,0);this._set(this.lib.ARM_REG_FAULTMASK,0);this._set(this.lib.ARM_REG_BASEPRI,0);this._set(this.lib.ARM_REG_MSP,vectors.stack);this._set(this.lib.ARM_REG_SP,vectors.stack);
    this._set(this.lib.ARM_REG_PC,vectors.reset&~1);
    this._set(this.lib.ARM_REG_LR,0xffffffff);
    // Cortex-M4 needs xPSR.T. CPSR is not the M-profile architectural state.
    if(this.lib.ARM_REG_XPSR!==undefined)this._set(this.lib.ARM_REG_XPSR,0x01000000);
    else if(this.lib.ARM_REG_CPSR!==undefined)this._set(this.lib.ARM_REG_CPSR,0x01000020);
    this.instructionCount=this.debug?0:null;this.runs=0;this.lastBudget=0;this.started=true;this.stop=null;this.modelError=null;this.lastFault=null;this.trace=[];this.lastPc=vectors.reset&~1;
    return vectors;
  }
  setDebug(v){
    this.debug=!!v;
    if(this.debug&&!this.debugHook&&this.lib.HOOK_CODE!==undefined){
      this.instructionCount=0;
      this.debugHook=this.uc.hook_add(this.lib.HOOK_CODE,(_engine,address,size)=>{
        this.instructionCount++;
        const pc=Number(address)>>>0;let opcode=0;
        try{const bytes=this.uc.mem_read(pc,Number(size));for(let i=0;i<bytes.length;i++)opcode=(opcode|(bytes[i]<<(i*8)))>>>0;}catch{}
        this.trace.push({pc,opcode,size:Number(size),asm:Number(size)+' octets · entrée observée'});
        if(this.trace.length>200)this.trace.shift();
      },null,1,0);
    }else if(!this.debug&&this.debugHook){
      this.uc.hook_del?.(this.debugHook);
      this.debugHook=null;this.instructionCount=null;this.trace=[];
    }
  }
  run({budget=200000,breakpoint=null,step=false}={}){
    if(!this.started)throw new Error('Reset necessaire');
    if(this.stop&&!['control','waiting'].includes(this.stop.category))return this.state(); // A model boundary is terminal until reset; never continue after a placeholder read.
    const count=step?1:Math.min(2000000,Math.max(1,Math.floor(budget)));
    const pc=this._get(this.lib.ARM_REG_PC);
    this.lastFault=null;this.modelError=null;this.stop=null;
    try{
      const limit=this.hardware.steps+count;let sleeps=0;
      while(this.hardware.steps<limit&&!this.modelError){
        if(this.resetRequest){const cause=this.resetRequest.source;this.reset(FLASH_START,{system:true,cause});continue;}
        if(this.sleeping){const e=this.hardware.selectedInterrupt();if(e!==null){this.sleeping=false;this.enterException(e);}else if(this.eventRegister){this.sleeping=false;this.eventRegister=false;}else{const delay=this.hardware.wakeDelay();if(!Number.isFinite(delay)||++sleeps>100000){this.stop={category:'waiting',reason:'WFI/WFE : attente d’une entrée physique ou interruption',pc:this._get(this.lib.ARM_REG_PC)};break;}this.hardware.advance(Math.min(delay,this.hardware.nextDelay()));continue;}}
        this.internalStop=null;this.uc.emu_start(this._get(this.lib.ARM_REG_PC)|1,breakpoint===null?0:(breakpoint&~1),0,Math.max(1,limit-this.hardware.steps));
        if(this.modelError)break;
        if(this.internalStop==='exception-return')this.exitException();
        else if(this.internalStop?.exception!==undefined)this.enterException(this.internalStop.exception);
        else if(this.internalStop==='sleep')continue;
        else break;
      }
      this.runs++;this.lastBudget=count;
      this.stop=this.modelError?{category:'model_incomplete',reason:this.modelError.reason,pc:this._get(this.lib.ARM_REG_PC),
        ...(this.modelError.instructionBoundary?{}:{fault:{address:this.modelError.address,size:this.modelError.size}}),hint:this.modelError.instructionBoundary?'Instruction d’attente décodée ; le modèle de réveil par interruption reste à développer.':'Peripherique non modelise par le banc Web. Pas de retour arbitraire.'}:this.stop;
    }catch(err){
      const fault=this.lastFault;
      const peripheral=fault&&(fault.address>=0x40000000&&fault.address<0x60000000 || fault.address>=0xe0000000&&fault.address<0xe0100000);
      this.stop={category:peripheral?'model_incomplete':'cpu_or_peripheral_error',
        reason:String(err?.message??err),pc:this._get(this.lib.ARM_REG_PC),
        ...(fault?{fault}:{}),
        hint:peripheral?'Acces a un peripherique absent ou insuffisamment modele: reprendre le modele correspondant du banc Python V11.8.':'Verifier le PC, le vecteur de reset et les instructions a cette adresse.'};
    }
    if(!this.stop&&breakpoint!==null&&this._get(this.lib.ARM_REG_PC)===(breakpoint&~1))this.stop={category:'control',reason:'Point d’arrêt atteint',pc:this._get(this.lib.ARM_REG_PC)};
    if(this.stop){
      const faultPc=this.stop.pc??this._get(this.lib.ARM_REG_PC);
      try{this.stop.instructionHex=Array.from(this.uc.mem_read(faultPc&~1,8),b=>b.toString(16).padStart(2,'0')).join(' ');}catch{}
      this.stop.cpuModel=this.cpuModelName;
      if(this.lib.ARM_REG_XPSR!==undefined){try{this.stop.xpsr=this._get(this.lib.ARM_REG_XPSR);}catch{}}
    }
    this.lastPc=this._get(this.lib.ARM_REG_PC);return this.state();
  }
  memory(address,length){return toArray(this.uc.mem_read(address>>>0,length));}
  state(){let flags=null;if(this.debug&&this.lib.ARM_REG_XPSR!==undefined){const x=this._get(this.lib.ARM_REG_XPSR);flags={N:x>>>31,Z:(x>>>30)&1,C:(x>>>29)&1,V:(x>>>28)&1,Q:(x>>>27)&1,T:(x>>>24)&1,IPSR:x&511};}
    const regs=this.debug?Array.from({length:16},(_,i)=>this._get(this.lib[`ARM_REG_R${i}`]??(i===13?this.lib.ARM_REG_SP:i===14?this.lib.ARM_REG_LR:this.lib.ARM_REG_PC))):null;
    return {coreRevision:this.coreRevision,cpuModel:this.cpuModelName,cpuModelId:this.cpuModelId,system:this.boot.status(),resets:{generation:this.resetGeneration??0,events:this.resetEvents??[]},hardware:{IPSR:this._get(this.lib.ARM_REG_IPSR),CONTROL:this._get(this.lib.ARM_REG_CONTROL),PRIMASK:this._get(this.lib.ARM_REG_PRIMASK),BASEPRI:this._get(this.lib.ARM_REG_BASEPRI),virtualUnits:this.time,instructionEntries:this.hardware.steps,sleeping:this.sleeping,interrupts:this.irqLog.length,SysTickWraps:this.hardware.wraps,ADCTransfers:this.hardware.adc.total},pc:this.started?this._get(this.lib.ARM_REG_PC):0,count:this.instructionCount,runs:this.runs,lastBudget:this.lastBudget,regs,stop:this.stop,flags,trace:this.debug?this.trace.slice():[],writes:[]};
  }
  close(){this.uc.close?.();}
}
