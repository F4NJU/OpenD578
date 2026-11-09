import {powerCalibrationStatus} from './rf-commands.mjs?build=web0160r1';
import {serviceCalibrationStatus} from './calibration-status.mjs?build=web0160r1';
import {NandReadProvenance} from './nand-provenance.mjs?build=web0160r1';
/* Browser WASM runtime. No JavaScript Thumb interpreter is constructed or used.
 * OpenD578 hardware model reuses physical memory and NAND storage contracts.
 * Copyright (c) 2026 OpenD578 contributors; GPL-3.0-or-later.
 */
import {panelStatus} from './panel-status.mjs?build=web0160r1';
import {unhex} from './usb-device.mjs?build=web0160r1';
import {setSensorInputs,sensorStatus} from './sensor-inputs.mjs?build=web0160r1';
import {MemoryBus,checkVector,FLASH_START,FLASH_SIZE,APPLICATION_DEFAULT,parseAddress,hex} from './memory.mjs?build=web0160r1';
import {NandOverlay} from './nand.mjs?build=web0160r1';
import {sha256File} from './sha256.mjs?build=web0160r1';
import {BoardIO} from './board-io.mjs?build=web0160r1';
import {UnicornCortexM4} from './unicorn-cortex.mjs?build=web0160r1';
export class WasmMachine {
  constructor({factory,debug=false}={}) {
    this.factory=factory;this.debug=!!debug;this.bus=new MemoryBus({traceWrites:false});
    this.nand=new NandOverlay();this.board=new BoardIO();this.core=null;this.entries=[];
    this.files={};this.hashes={};this.diagnostics=[];this.address=APPLICATION_DEFAULT;
    this.selectedVector=null;this.started=false;
  }
  async attach({flash=null,boot=null,app=null,nand=null,oob=null,ecc=null,appAddress=APPLICATION_DEFAULT}={}){
    this.core?.close();this.core=null;this.bus=new MemoryBus();this.nand=new NandOverlay();
    this.board=new BoardIO({nandStorage:this.nand});this.nandProvenance=new NandReadProvenance();this.board.nand.onRead=e=>this.nandProvenance.observe(e,this.core?.time??null);this.files={flash,boot,app,nand,oob,ecc};this.hashes={};
    this.entries=[];this.diagnostics=[];this.address=parseAddress(appAddress);
    this.started=false;this.selectedVector=null;
    for(const [role,file,address] of [['flash',flash,FLASH_START],['boot',boot,FLASH_START],['app',app,this.address]]){
      if(!file)continue;
      if(role==='flash'&&file.size!==FLASH_SIZE)throw new Error('La Flash complete doit faire 3 Mio');
      if(file.size<8||file.size>FLASH_SIZE)throw new Error(`${role}: longueur invalide`);
      const data=new Uint8Array(await file.arrayBuffer());
      const layout=this.bus.loadFlash(data,address,role),vectors=checkVector(data,address);
      this.entries.push({role,name:file.name,length:file.size,address,vectors,overlaps:layout.overlaps});
      if(layout.overlaps.length)this.diagnostics.push(`${role} remplace des octets de ${layout.overlaps.join(', ')}`);
      if(!vectors.ok)this.diagnostics.push(`${role}: ${vectors.issues.join('; ')}`);
      if(file.size<=16*1024*1024)this.hashes[role]=await sha256File(file);
    }
    for(const [zone,file] of [['main',nand],['oob',oob],['ecc',ecc]])this.nand.attach(zone,file);
    if(!this.factory)throw new Error('Unicorn ARM WebAssembly non installe : lancer tools/vendor_unicorn_arm.sh');
    const library=await this.factory();
    this.core=new UnicornCortexM4(library,{board:this.board,debug:this.debug});
    this.core.loadFlash(this.bus.flash);
    if(nand)this.diagnostics.push('NAND connectee au bus GPIO SPI PB8/PB14/PB15 et PA15; lectures par FileReaderSync dans le Web Worker');
    return this.status();
  }
  volumePcmInput(config){if(!this.core)throw Error('Charger le firmware');if(config)this.board.volumePcm.configure(config,this.core.time);else this.board.volumePcm.clear();return this.status();}
  volumePcmCapture(){if(!this.core)throw Error('Charger le firmware');return this.board.volumePcm.capture(this.core.time);}
  audioInput(config){if(!this.core)throw Error('Charger le firmware');if(config)this.board.audioInput.configure(config,this.core.time);else this.board.audioInput.clear();return this.status();}
  audioInputCapture(){return {status:this.board.audioInput.status(),samples:this.board.audioInput.observed.slice()};}
  rfInputs(bank,registers){if(!this.core)throw Error('Charger les images');this.core.hardware.rf.setInputs(bank,registers);return this.status();}
  gpsScenario(config){const h=this.core?.hardware;if(!h)throw new Error('Initialiser le CPU');h.gps.configure(config,this.core.time);h.gps.advance(this.core.time,h.serial.get(0x40004400).device);h.nextDevices=this.core.time+1;return this.status();}
  sensorInputs(values){if(!this.core)throw Error('Charger les images avant les mesures ADC');setSensorInputs(this.board,values);return this.status();}
  usbConnect(){const h=this.core?.hardware;if(!h)throw new Error('Initialiser le CPU');h.startUsb();return this.status();}
  usbDisconnect(){const h=this.core?.hardware;if(!h)throw new Error('Initialiser le CPU');h.stopUsb();return this.status();}
  cpsWrite(address,hexBytes){const h=this.core?.hardware;if(!h)throw new Error('Initialiser le CPU');h.cps.startWrite(parseAddress(address),unhex(hexBytes.replace(/\s/g,'')),this.core.time);return this.status();}
  cpsRename(name){const h=this.core?.hardware;if(!h)throw Error('Initialiser le CPU');h.cpsEdit.rename(name,this.core.time);return this.status();}
  cpsVerify(){const h=this.core?.hardware;if(!h)throw Error('Initialiser le CPU');h.cpsEdit.verify(this.core.time);return this.status();}
  cpsRestore(){const h=this.core?.hardware;if(!h)throw Error('Initialiser le CPU');h.cpsEdit.restore(this.core.time);return this.status();}
  cpsBackup(){return this.core.hardware.cpsEdit.backup();}
  cpsReadBytes(){const c=this.core?.hardware.cps;if(!c||c.state!=='complete'||!c.blocks.length)throw Error('Aucune lecture CPS complète');return Uint8Array.from(c.blocks.flatMap(b=>Array.from(unhex(b.hex))));}
  cpsRead(address,length=16){const h=this.core?.hardware;if(!h)throw new Error('Initialiser le CPU');if(h.cpsEdit.active||h.cpsEdit.state==='awaiting_verification')throw Error('Terminer la transaction mémoire CPS');h.cps.startRead(parseAddress(address),length,this.core.time);return this.status();}
  setDebug(enabled){this.debug=!!enabled;this.core?.setDebug(enabled);return this.status();}
  vectorFor(mode='auto'){
    const roles=this.entries.map(e=>e.role);
    if(mode==='boot'){if(!roles.includes('boot')&&!roles.includes('flash'))throw new Error('Bootloader absent');return FLASH_START;}
    if(mode==='app'){if(!roles.includes('app')&&!roles.includes('flash'))throw new Error('Application absente');return this.address;}
    if(mode==='flash'){if(!roles.includes('flash'))throw new Error('Flash complete absente');return FLASH_START;}
    if(mode!=='auto')throw new Error('Mode reset inconnu');
    if(roles.includes('boot')||roles.includes('flash'))return FLASH_START;
    if(roles.includes('app'))return this.address;
    throw new Error('Charger un bootloader, un firmware ou une Flash');
  }
  reset(mode='auto'){
    if(!this.core)throw new Error('Charger le moteur WASM avant reset');
    const address=this.vectorFor(mode);this.nandProvenance=new NandReadProvenance();this.core.reset(address);
    this.started=true;this.selectedVector=address;return this.status();
  }
  step(){if(!this.core)throw new Error('Core absent');this.core.run({step:true});return this.status();}
  run(budget=200000,breakpoint=null){if(!this.core)throw new Error('Core absent');this.core.run({budget,breakpoint});return this.status();}
  powerPulse(){if(!this.core)throw new Error('Charger les images');this.board.setKey('POWER',true);this.core.hardware.powerReleaseAt=this.core.time+240000000;return this.status();}
  panelKey(name,down,minimumMs=name==='POWER'?2000:200){if(!Number.isFinite(minimumMs)||minimumMs<20||minimumMs>10000)throw Error('Durée d’appui : 20 à 10000 ms');if(!this.core)throw new Error('Charger les images');const h=this.core.hardware;if(down){h.keyRelease.delete(name);h.keyMinimum.set(name,this.core.time+Math.round(minimumMs*120000));this.board.setKey(name,true);}else{const at=h.keyMinimum.get(name)??this.core.time;if(this.core.time>=at)this.board.setKey(name,false);else h.keyRelease.set(name,at);}return this.status();}
  setKey(name,down){this.board.setKey(name,down);return this.status();}
  rotate(direction){this.board.rotate(direction);return this.status();}
  setVolume(which,value){this.board.setVolume(which,value);return this.status();}
  micPress(key){if(!this.core)throw Error('Charger les images');this.syncMic();const raw=this.board.mic.input(key,this.core.time);this.syncMic();return {sent:raw?Array.from(raw):[],board:this.board.status()};}
  syncMic(){const h=this.core.hardware,d=h.serial.get(0x40013800).device;this.board.mic.advance(this.core.time,d);h.nextDevices=this.core.time+1;}
  micConfigure(options){if(!this.core)throw Error('Charger les images');const was=this.board.mic.connected;this.board.mic.configure(options,this.core.time);if(was&&!this.board.mic.connected)this.core.hardware.serial.get(0x40013800).device.wire=[];this.syncMic();return this.status();}
  micReleaseAll(){if(!this.core)throw Error('Charger les images');this.board.mic.releaseAll(this.core.time);this.syncMic();return this.status();}
  gpsInject(sentence,sourceBaud=null){
    if(!this.core)throw new Error('Charger les images avant GPS');if(sourceBaud!==null&&![4800,9600,19200,38400,57600,115200].includes(sourceBaud))throw Error('Débit NMEA externe invalide');
    this.board.injectGpsNmea(sentence);const d=this.core.hardware.serial.get(0x40004400).device;d.advance(this.core.time);d.schedule(this.board.gpsRx.splice(0),sourceBaud===null?{}:{at:this.core.time,byteSteps:120000000*10/sourceBaud});this.core.hardware.nextDevices=this.core.time+1;
    return this.status();
  }
  lcd(){const s=this.board.lcd.snapshot();return {...s,backlight:this.board.lcdBacklight};}
  readMemory(addr,length=64){if(!this.core)throw new Error('Core absent');const address=parseAddress(addr);return {address,bytes:Array.from(this.core.memory(address,length)),label:'Memoire physique Unicorn WASM'};}
  filesInfo(){return Object.fromEntries(Object.entries(this.files).map(([role,file])=>[role,file?{name:file.name,size:file.size,sha256:this.hashes[role]??null,hashed:!!this.hashes[role]}:null]));}
  status(){return {VOLUME_PCM:this.board.volumePcm.status(),AUDIO_INPUT:this.board.audioInput.status(),engine:'browser-wasm-d578-0.16.0',capability:'unicorn_arm_thumb2_wasm',debugEnabled:this.debug,
    scope:{dmr:'deferred',dmrSubstitutionAllowed:true,dmrSubstitutionConnected:true,nonDmrSubstitutionAllowed:false},
    RF_COMMANDS:this.core?{frequencies:this.core.hardware.rf.frequencyCommands.status(this.hashes.flash),dac0:this.core.hardware.dac[0x42c]??null,calibration:powerCalibrationStatus(this.nandProvenance,this.hashes.flash)}:null,AUDIO_CALIBRATION:this.nandProvenance?serviceCalibrationStatus(this.nandProvenance,this.hashes.flash):null,NAND_PROVENANCE:this.nandProvenance?.status()??null,FACADE:panelStatus(this.board,this.core?.hardware,this.hashes.flash),SENSORS:sensorStatus(this.board,this.core?.hardware),GPS:this.core?.hardware.gps.status()??null,USB:this.core?{cdc:this.core.hardware.cdc.status(),cps:this.core.hardware.cps.status(),memory:this.core.hardware.cpsEdit.status()}:null,model:'D578UV PRO GD32 (portage peripheriques de demarrage)',entries:this.entries,diagnostics:this.diagnostics,
    files:this.filesInfo(),nand:this.nand.summary(),board:this.board.status(),selectedVector:this.selectedVector,
    cpu:this.core?.state()??{pc:0,count:0,stop:null},started:this.started,
    limitations:[
      'Temps en unités d’instruction, sans précision au cycle ; domaine RTC et entrées ADC explicitement configurés',
      'Exceptions de base uniquement : pas d’imbrication ni de frames FPU ; DMA moteur ADC0/ch0',
      'RF et audio PCM non qualifiés de bout en bout ; contrôles numériques RF/FM/codec portés',
      'DMR différé : protocole HPI et remplacement de version déclaré, DSP/vocodeur non exécuté',
      'USB/CPS : nom CH1 contrôlé par relecture de 128 Kio après reset ; CPS général et pont série système hors qualification ; Bluetooth non raccordé',
      'LCD compatible avec les commandes observées ; composant exact et colorimétrie physique à qualifier'
    ]};}
  async hash(role,progress=null){const file=this.files[role];if(!file)throw new Error('Fichier absent: '+role);
    this.hashes[role]=await sha256File(file,progress);return {role,sha256:this.hashes[role],bytes:file.size};}
  report({includeTrace=false}={}){return {schema:'opend578.browser-report.v1',createdAt:new Date().toISOString(),engine:'browser-wasm-d578-0.16.0',capability:'unicorn_arm_thumb2_wasm',
    warning:'Démarrage et interface OEM vérifiables ; les fonctions radio et la totalité des périphériques restent à qualifier',
    board:'D578UV PRO GD32',images:this.filesInfo(),segments:this.entries,selectedVector:this.selectedVector,
    RFcommands:this.status().RF_COMMANDS,audioCalibration:this.nandProvenance?serviceCalibrationStatus(this.nandProvenance,this.hashes.flash):null,nandReadProvenance:this.nandProvenance?.status()??null,scope:this.status().scope,panel:panelStatus(this.board,this.core?.hardware,this.hashes.flash),sensors:sensorStatus(this.board,this.core?.hardware),debugEnabled:this.debug,cpu:this.core?.state()??null,nand:this.nand.summary(),hardware:this.board.status(),
    hardwareRuntime:this.core?.hardware.status()??null,interrupts:this.core?.irqLog??[],diagnostics:this.diagnostics,incomplete:this.status().limitations};}
}
