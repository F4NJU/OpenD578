/* Worker runtime: all CPU execution stays on the visitor's machine. */
import {WasmMachine} from './wasm-machine.mjs?build=web0151r3';
import {parseAddress} from './memory.mjs?build=web0151r3';
import {bindPatchSources,validatePatchSources} from './session-patch.mjs?build=web0151r3';
const WORKER_REVISION='web0151r3';
let machine = new WasmMachine({factory:()=>self.__wasmFactory()});
let commandQueue=Promise.resolve();
self.onmessage=event=>{commandQueue=commandQueue.then(()=>dispatch(event)).catch(error=>self.postMessage({id:event.data?.id,ok:false,error:String(error)}));};
async function dispatch({data}){
  const {id,command,args={}}=data??{};
  try{
    let result;
    switch(command){
      case 'version':result={build:WORKER_REVISION,engine:machine.status().engine,source:'worker'};break;
      case 'audioInput':result=machine.audioInput(args.config);break;
      case 'audioInputCapture':result=machine.audioInputCapture();break;
      case 'status':result=machine.status();break;
      case 'load':{const next=new WasmMachine({factory:()=>self.__wasmFactory(),debug:machine.debug});try{result=await next.attach(args);}catch(error){next.core?.close();throw error;}const previous=machine;machine=next;previous.core?.close();break;}
      case 'setDebug':result=machine.setDebug(args.enabled);break;
      case 'reset':result=machine.reset(args.mode);break;
      case 'step':result=machine.step();break;
      case 'run':result=machine.run(args.budget,args.breakpoint===null||args.breakpoint===undefined?null:parseAddress(args.breakpoint));break;
      case 'readMemory':result=machine.readMemory(args.address,args.length);break;
      case 'gpsScenario':result=machine.gpsScenario(args.config);break;
      case 'usbConnect':result=machine.usbConnect();break;
      case 'usbDisconnect':result=machine.usbDisconnect();break;
      case 'cpsWrite':result=machine.cpsWrite(args.address,args.hex);break;
      case 'cpsRename':result=machine.cpsRename(args.name);break;
      case 'cpsVerify':result=machine.cpsVerify();break;
      case 'cpsRestore':result=machine.cpsRestore();break;
      case 'cpsBackup':result=machine.cpsBackup();break;
      case 'cpsReadBytes':result=machine.cpsReadBytes();break;
      case 'cpsRead':result=machine.cpsRead(args.address,args.length);break;
      case 'powerPulse':result=machine.powerPulse();break;
      case 'panelKey':result=machine.panelKey(args.name,args.down,args.minimumMs);break;
      case 'boardKey':result=machine.setKey(args.name,args.down);break;
      case 'boardRotate':result=machine.rotate(args.direction);break;
      case 'boardVolume':result=machine.setVolume(args.which,args.value);break;
      case 'sensorInputs':result=machine.sensorInputs(args.values);break;
      case 'micKey':result=machine.micPress(args);break;
      case 'rfInputs':result=machine.rfInputs(args.bank,args.registers);break;
      case 'micConfigure':result=machine.micConfigure(args);break;
      case 'micReleaseAll':result=machine.micReleaseAll();break;
      case 'gpsInject':result=machine.gpsInject(args.sentence,args.baud??null);break;
      case 'lcd':result=machine.lcd();break;
      case 'readNand':{
        const page=Number(args.page);const {bytes,source}=await machine.nand.readPage(args.zone,page);
        result={zone:args.zone,page,bytes:Array.from(bytes),source,nand:machine.nand.summary()};break;
      }
      case 'programNand':{
        const written=await machine.nand.program(args.zone,Number(args.page),Number(args.offset),Uint8Array.from(args.bytes));
        result={bytes:Array.from(written.bytes),source:written.source,nand:machine.nand.summary()};break;
      }
      case 'eraseNand':result={...await machine.nand.erase(Number(args.block)),nand:machine.nand.summary()};break;
      case 'exportPatch':result=await bindPatchSources(machine.nand.exportPatch(),machine.files,async role=>machine.hashes[role]??(await machine.hash(role,(done,total)=>self.postMessage({type:'progress',id,role,done,total}))).sha256);break;
      case 'importPatch':{
        await validatePatchSources(args.patch,machine.files,async role=>machine.hashes[role]??(await machine.hash(role,(done,total)=>self.postMessage({type:'progress',id,role,done,total}))).sha256);
        result={...machine.nand.importPatch(args.patch),nand:machine.nand.summary()};
        machine.reset('auto');break;
      }
      case 'hash':result=await machine.hash(args.role,(done,total)=>self.postMessage({type:'progress',id,command,role:args.role,done,total}));break;
      case 'report':result=machine.report(args);break;
      default:throw new Error('Commande inconnue: '+command);
    }
    self.postMessage({id,ok:true,result});
  }catch(error){self.postMessage({id,ok:false,error:error?.message||String(error),category:error.category??'execution_error'});}
}
