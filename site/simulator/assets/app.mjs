import {pcm16Wav} from './audio-volume-stream.mjs?build=web0151r5';
import {wavToAdcCodes,decodePcm16Wav} from './audio-pcm-input.mjs?build=web0151r5';
import {rfCommandText} from './rf-commands.mjs?build=web0151r5';
import {audioControlText} from './audio-routing.mjs?build=web0151r5';
import {calibrationStatusText} from './calibration-status.mjs?build=web0151r5';
import {audioStatusText} from './audio-devices.mjs?build=web0151r5';
import {microphoneView} from './microphone-view.mjs?build=web0151r5';
import {antennaFrame} from './antenna-input.mjs?build=web0151r5';
/* OpenD578 local Web UI. All firmware and memory contents stay on the client.
 * Copyright (C) 2026 OpenD578 contributors. GPL-3.0-or-later.
 */
import { hex, parseAddress } from './memory.mjs?build=web0151r5';
import {landscapePixels} from './lcd-panel.mjs?build=web0151r5';
import {ExecutionLoop} from './execution-loop.mjs?build=web0151r5';
import {selectBackupSet,backupDescription} from './backup-set.mjs?build=web0151r5';
import {GuidedBoot} from './guided-boot.mjs?build=web0151r5';
const $ = id => document.getElementById(id);
const worker = new Worker(new URL('./engine.wasm.worker.js?build=web0151r5', import.meta.url));
let readyResolve,readyReject,busyLoading=false,selectedBackupArgs=null;
const runtimeReady=new Promise((resolve,reject)=>{readyResolve=resolve;readyReject=reject;});
const readyTimeout=setTimeout(()=>readyReject(new Error('Le moteur Web ne répond pas. Vérifier le chargement des fichiers du site, puis recharger la page.')),15000);
let requestId = 0;
const requests = new Map();
let status = null;
let attachedArgs = null;
let recordedActions = [];
let importedScenario = null;
let lastPage = null;
let scenarioTruncated=false;
let launchWallTime=null,launchVirtualTime=0;
const guidedBoot=new GuidedBoot({run:budget=>act('run',{budget,breakpoint:null}),powerPulse:()=>act('powerPulse'),onPower:()=>log('Démarrage guidé : Power transmis au premier sommeil du MCU, puis relâché après 2 secondes du banc.')});
const loop=new ExecutionLoop({
 run:budget=>guidedBoot.run(budget),
 onState:s=>{if(s.cpu?.stop)log('Arrêt du moteur : '+s.cpu.stop.reason,true);},
 onRunning:running=>{document.body.classList.toggle('continuous-running',running);$('guidedStart').disabled=running||busyLoading;$('loadSample').disabled=running||busyLoading;$('loadAudioAlpha').disabled=running||busyLoading;$('loadFiles').disabled=running||busyLoading;$('pauseContinuous').disabled=!running;$('startContinuous').disabled=running||!status?.started||!!status?.cpu?.stop&&!['waiting','control'].includes(status.cpu.stop.category);$('runStatus').textContent=running?'Processeur en cours d’exécution. Les commandes restent accessibles.':status?.cpu?.stop?'Arrêt : '+status.cpu.stop.reason:status?.started?'Processeur en pause.':'Chargez vos images, puis initialisez le processeur.';}
});
const TRACKED = new Set(['reset','step','run','readMemory','readNand','programNand','eraseNand','boardKey','boardRotate','boardVolume','micKey','gpsInject','powerPulse','panelKey','usbConnect','usbDisconnect','cpsRead','cpsWrite','cpsRename','cpsVerify','cpsRestore','gpsScenario','sensorInputs','micConfigure','micReleaseAll','rfInputs']);

function log(message, error = false) {
  const div = document.createElement('div');
  if (error) div.className = 'error';
  const t = document.createElement('time');
  t.textContent = new Date().toLocaleTimeString('fr-FR');
  div.append(t, document.createTextNode(message));
  $('events').prepend(div);
  while ($('events').children.length > 100) $('events').lastChild.remove();
}

worker.addEventListener('message', ({data}) => {
  if(data.type==='ready'){clearTimeout(readyTimeout);readyResolve(data);return;}
  if(data.type==='startup-error'){clearTimeout(readyTimeout);readyReject(new Error(data.error));return;}
  if (data.type === 'progress') {
    const percent = data.total ? Math.round(data.done / data.total * 100) : 100;
    $('hashProgress').textContent = `${data.role} : ${percent}% (${(data.done / 1048576).toFixed(1)} / ${(data.total / 1048576).toFixed(1)} Mio)`;
    return;
  }
  const pending = requests.get(data.id);
  if (!pending) return;
  requests.delete(data.id);
  if (data.ok) pending.resolve(data.result);
  else pending.reject(Object.assign(new Error(data.error), { category: data.category, address: data.address }));
});
worker.addEventListener('error', event => {
  clearTimeout(readyTimeout);readyReject(new Error(event.message));
  log(`Echec du moteur Web Worker : ${event.message}`, true);
  for (const pending of requests.values()) pending.reject(new Error(event.message));
  requests.clear();
});
async function send(command, args = {}) {
  await runtimeReady;
  return new Promise((resolve,reject) => {
    const id = ++requestId;
    requests.set(id, { resolve,reject });
    worker.postMessage({ id, command, args });
  });
}
function track(command,args) {
  if (!TRACKED.has(command)) return;
  if(recordedActions.length>=20000){if(!scenarioTruncated)log('Limite de 20 000 actions atteinte : scénario incomplet, export refusé.',true);scenarioTruncated=true;return;}
  recordedActions.push({ command, args: structuredClone(args) });
  renderScenario();
}
async function act(command, args = {}, {record = true} = {}) {
  const result = await send(command,args);
  if (record) track(command,args);
  if (['load','reset','step','run','setDebug','usbConnect','usbDisconnect','cpsRead','cpsWrite','cpsRename','cpsVerify','cpsRestore','gpsScenario','sensorInputs'].includes(command)) refresh(result);
  if (['programNand','eraseNand','importPatch'].includes(command)) {
    status = await send('status');
    refresh(status);
  }
  return result;
}
function safe(action) {
  return async () => {
    try { await action(); }
    catch (error) { $('runtimeState').textContent='Action interrompue : '+error.message;log(error.message==='Reset necessaire'?'Initialiser le processeur avec le bouton Reset avant Executer.':`${error.category ? `[${error.category}] ` : ''}${error.message}`, true); }
  };
}
function fileFor(id) { return $(id).files?.[0] ?? null; }
function fileInputs() {
  if(selectedBackupArgs)return selectedBackupArgs;
  return {
    flash:fileFor('flashFile'),boot:fileFor('bootFile'),app:fileFor('appFile'),
    nand:fileFor('nandFile'),oob:fileFor('oobFile'),ecc:fileFor('eccFile'),
    appAddress:parseAddress($('appAddress').value)
  };
}
async function loadImages(args, label) {
  guidedBoot.cancel();await loop.pause();micHeld.clear();launchWallTime=null;
  const s = await act('load',args,{record:false});
  attachedArgs = args;
  recordedActions = [];scenarioTruncated=false;
  importedScenario = null;
  $('replayScenario').disabled = true;
  renderScenario();
  $('memoryDump').textContent = 'Cliquez sur Lire.';
  $('nandDump').textContent = 'Cliquez sur Lire page.';
  lastPage = null;lastLcdWrites=-1;
  log(`${label} : ${s.entries.length} segment(s) Flash, ${Object.values(s.files).filter(Boolean).length} fichier(s) charge(s).`);
  for (const warning of s.diagnostics) log(`Limite / chevauchement : ${warning}`);
}
function beginContinuous(){
 if(launchWallTime===null){launchWallTime=performance.now();launchVirtualTime=status?.cpu?.hardware?.virtualUnits??0;}
 void loop.start(numberIn($('budget').value,1,1000000)).catch(error=>log(error.message,true));
}
function renderScenario() {
  $('scenarioActions').textContent = recordedActions.length ? recordedActions.slice(-100).map((a,i)=>`${String(Math.max(0,recordedActions.length-100)+i+1).padStart(3)} ${a.command} ${JSON.stringify(a.args)}`).join('\n') : 'Aucune action.';
}
function refresh(s) {
  if (!s || !s.cpu) return;
  status = s;
  const virtualSeconds=(s.cpu?.hardware?.virtualUnits??0)/120000000;
  const elapsed=launchWallTime===null?null:(performance.now()-launchWallTime)/1000;
  $('executionProgress').textContent=`Temps du banc : ${virtualSeconds.toFixed(2)} s`+(elapsed!==null?` · temps écoulé : ${elapsed.toFixed(1)} s · vitesse moyenne : ${((virtualSeconds-launchVirtualTime/120000000)/Math.max(elapsed,0.001)).toFixed(3)}×`:'')+` · écritures LCD : ${(s.board?.lcd?.writes??0).toLocaleString('fr-FR')}`;
  if(s.VOLUME_PCM){const v=s.VOLUME_PCM;$('volumePcmState').textContent=v.connected?`${v.ports.join(' / ')} · ${v.processed}/${v.total} échantillons · ${v.gainChanges} commandes pendant le clip`:'Aucune source U2429.';}
  if(s.AUDIO_INPUT){const a=s.AUDIO_INPUT;$('audioInputState').textContent=a.connected?`PC0 / ADC10 : ${a.length} échantillons source à ${a.sampleRate} Hz · ${a.converted} conversions · ${a.captured} acquisitions conservées${a.captureTruncated?' (capture bornée)':''}\nLe trajet voix FM reste distinct de cette entrée.`:'Aucune source PCM externe.';}
  if(s.RF_COMMANDS)$('rfCommandState').textContent=rfCommandText(s.RF_COMMANDS);if(s.SENSORS){const p=s.SENSORS;$('sensorState').textContent=`ADC6 : ${p.adc[6]} · ADC10 : ${p.adc[10]} · ADC11 : ${p.adc[11]}\nSorties DAC0 / DAC1 : ${p.dac0??'—'} / ${p.dac1??'—'} bruts\nRF banque 0 / page 0 / registre 0x25 : ${p.fanRegister===null?'non écrit':hex(p.fanRegister)} · bit ventilateur : ${p.fanBit===null?'inconnu':p.fanBit?'1':'0'}\nSWR / ROS : raccordement non qualifié`;}
  const edit=s.USB?.memory;const busy=edit&&['backup','writing','waiting_reset','restarting','verifying','awaiting_verification'].includes(edit.state);
  const cdc=s.USB?.cdc,cps=s.USB?.cps;if(s.GPS)renderGps(s.GPS,s.cpu?.hardware?.UART??s.hardware?.UART);if(s.FACADE)renderPanel(s.FACADE);if(s.AUDIO_CALIBRATION)$('calibrationState').textContent=calibrationStatusText(s.AUDIO_CALIBRATION);
  $('usbConnect').disabled=!s.started||!!cdc&&!['disconnected','error'].includes(cdc.state);$('usbDisconnect').disabled=!s.started||!cdc||cdc.state==='disconnected';$('cpsRead').disabled=!s.started||cdc?.state!=='ready'||cps?.state==='running'||!!busy;
  $('cpsRename').disabled=!s.started||cdc?.state!=='ready'||cps?.state==='running'||edit?.state!=='idle';
  $('cpsVerify').disabled=edit?.state!=='awaiting_verification';$('cpsRestore').disabled=edit?.state!=='verified';$('cpsBackup').disabled=!edit?.backupAvailable;
  const labels={idle:'Aucune modification',backup:'Lecture de la sauvegarde complète',writing:'Écriture par le firmware',waiting_reset:'END acquitté ; attente du watchdog',restarting:'Redémarrage et réénumération USB',awaiting_verification:'Attendez l’écran principal OEM, puis cliquez sur Vérifier',verifying:'Relecture complète après reset',verified:'Nom et bloc vérifiés après reset',restored:'Bloc d’origine restauré et vérifié',error:'Échec de vérification'};
  $('cpsMemoryState').textContent=edit?`${labels[edit.state]??edit.state}${edit.error?' · '+edit.error:''}\n${edit.progress?.total?'Transferts restants : '+edit.progress.remaining+' / '+edit.progress.total:''}${edit.evidence?'\n'+JSON.stringify(edit.evidence,null,2):''}`:'Aucune session CPS.';
  if(cdc){$('usbStatus').textContent=`USB CDC : ${cdc.state}${cdc.transfer?' · '+cdc.transfer:''}${cdc.error?' · '+cdc.error:''}\nTX hôte : ${cdc.sentTotal} octets · RX firmware : ${cdc.receivedTotal} octets\nDescripteur du firmware : ${cdc.deviceDescriptor||'en attente'}`;
    $('cpsResult').textContent=cps?`CPS : ${cps.state}${cps.operation?' · '+cps.operation:''}${cps.error?' · '+cps.error:''}\nModèle : ${cps.identity?.model??'en attente'}\n`+cps.blocks.map(b=>hex(b.address)+'  '+b.hex.match(/../g).join(' ')+'  '+new TextDecoder().decode(Uint8Array.from(b.hex.match(/../g),v=>parseInt(v,16))).replace(/[^ -~]/g,'.')).join('\n'):'Aucune lecture CPS.';
  }

  $('startContinuous').disabled=loop.running||!s.started||!!s.cpu.stop&&!['waiting','control'].includes(s.cpu.stop.category);
  if(!loop.running)$('runStatus').textContent=s.cpu.stop?'Arrêt : '+s.cpu.stop.reason:s.started?'Processeur prêt. Démarrez en continu ou exécutez un budget.':s.entries?.length?'Images chargées. Cliquez sur Reset pour initialiser le processeur.':'Sélectionner vos sauvegardes ou lancer le test CPU/LCD.';
  const cpu=s.cpu;
  $('cpuState').textContent = !s.started ? 'Non initialisé' : (cpu.stop ? cpu.stop.category : loop.running?'En cours':'Prêt / en pause');
  $('pcStat').textContent = s.started ? hex(cpu.pc) : '—';
  if($('startupState')){const sys=cpu.system??{},spi=s.board?.nandSpi??{};
    $('startupState').textContent=`CPU: ${cpu.cpuModel??'?'}\nRCU CTL: ${hex(sys.rcuControl??0)} · CFG: ${hex(sys.rcuConfig??0)}\nVTOR: ${hex(sys.vtor??0)} · SysTick: ${hex(sys.systickControl??0)}\nNAND GPIO: ${spi.transactions??0} transactions · derniere commande: ${spi.lastCommand===null||spi.lastCommand===undefined?'aucune':'0x'+spi.lastCommand.toString(16)} · lectures: ${spi.readBytes??0} octets\nTemps virtuel: ${((cpu.hardware?.virtualUnits??0)/120000000).toFixed(3)} s · interruptions conservées: ${cpu.hardware?.interrupts??0} · DMA ADC: ${cpu.hardware?.ADCTransfers??0} transferts\nGPS USART1 RX: ${s.board?.gps?.queued??0} octets`; }
  $('countStat').textContent = cpu.count===null || cpu.count===undefined?'Non mesure':cpu.count.toLocaleString('fr-FR');
  renderBoard(s.board);
  $('nandStat').textContent = s.nand.overlayPages.toLocaleString('fr-FR');
  const regs=$('registers');
  regs.replaceChildren();
  if (s.debugEnabled && cpu.regs) {
    for (let i=0;i<16;i++) {
      const item=document.createElement('div'); item.className='reg';
      const title=document.createElement('b'); title.textContent = i===13?'SP':i===14?'LR':i===15?'PC':`R${i}`;
      const value=document.createElement('span'); value.textContent=hex(cpu.regs[i]);
      item.append(title,value);regs.append(item);
    }
  } else regs.textContent='Mode debug désactivé.';
  $('flags').textContent = cpu.flags ? Object.entries(cpu.flags).map(([k,v])=>`${k}=${Number(v)}`).join('    ') : 'Mode debug désactivé.';
  const stop=$('stopReason');
  stop.className='stop-card'+(cpu.stop?.category==='model_incomplete'?' warning':cpu.stop?.category==='control'?' success':'');
  stop.textContent = cpu.stop ? `${cpu.stop.category}: ${cpu.stop.reason}${cpu.stop.pc !== undefined ? ` | PC ${hex(cpu.stop.pc)}` : ''}${cpu.stop.fault ? ` | Acces invalide ${hex(cpu.stop.fault.address)} (${cpu.stop.fault.size} octet(s))` : ''}${cpu.stop.hint ? ` | ${cpu.stop.hint}` : ''}${cpu.stop.cpuModel ? ` | Mode CPU: ${cpu.stop.cpuModel}` : ''}${cpu.stop.xpsr!==undefined ? ` | xPSR: ${hex(cpu.stop.xpsr)}` : ''}${cpu.stop.instructionHex ? ` | Octets: ${cpu.stop.instructionHex}` : ''}` : (s.started?'CPU initialise. Utiliser Executer.':'Charger les images, puis cliquer sur Reset avant Executer.');
  $('segments').textContent = s.entries.length ? s.entries.map(e=>{
    const vectors=e.vectors;
    return `${e.role.toUpperCase()} · ${e.name}\n  Charge : ${hex(e.address)} · ${e.length.toLocaleString('fr-FR')} o\n  SP: ${vectors.stack===null?'—':hex(vectors.stack)} · Reset: ${vectors.reset===null?'—':hex(vectors.reset)}\n  ${vectors.ok?'Vecteurs plausibles (non qualifies)':'ATTENTION '+vectors.issues.join('; ')}`;
  }).join('\n\n') : 'Aucun segment. NAND seule possible.';
  $('trace').textContent = cpu.trace?.length ? cpu.trace.map(t=>`${hex(t.pc)}  ${hex(t.opcode,4)}   ${t.asm}`).join('\n') : 'Aucune entrée d’instruction observée dans cette session de débogage.';
  $('writeLog').textContent = cpu.writes?.length ? cpu.writes.map(w=>`${hex(w.address)}  ${w.width} oct.  ${w.value}`).join('\n') : 'Suivi des écritures SRAM non raccordé ; la lecture mémoire reste disponible.';
  $('fileManifest').textContent = Object.entries(s.files).map(([key,file])=>file ? `${key.padEnd(6)} ${file.name} (${file.size.toLocaleString('fr-FR')} octets)\n       SHA-256: ${file.sha256 ?? 'non calcule'}` : `${key.padEnd(6)} non charge`).join('\n\n');
}
function dumpHex(bytes, base, preview = 256) {
  const end = Math.min(bytes.length,preview), lines=[];
  for(let i=0;i<end;i+=16){
    const slice=bytes.slice(i,i+16);
    const hexBytes=Array.from(slice,x=>x.toString(16).padStart(2,'0')).join(' ').padEnd(47,' ');
    const ascii=Array.from(slice,x=>x>=32&&x<127?String.fromCharCode(x):'.').join('');
    lines.push(`${hex(base+i)}  ${hexBytes}  |${ascii}|`);
  }
  if(bytes.length>end) lines.push(`... ${bytes.length-end} octets non affiches (la page entiere reste accessible).`);
  return lines.join('\n');
}
function saveJson(value,name) {
  const blob=new Blob([JSON.stringify(value,null,2)+'\n'],{type:'application/json'});
  saveBlob(blob,name);
}
function saveBlob(blob,name) {
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');a.href=url;a.download=name;
  document.body.append(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),30000);
}
function parseHexBytes(text) {
  const compact=text.trim().replace(/[\s,:-]+/g,'');
  if (!compact || compact.length%2 || compact.length>256 || !/^[a-f0-9]+$/i.test(compact)) throw new Error('Entrer entre 1 et 128 octets hexadecimaux complets');
  return Array.from({length:compact.length/2},(_,i)=>parseInt(compact.slice(2*i,2*i+2),16));
}
function numberIn(input,min,max) {
  const n=Number(input);
  if (!Number.isInteger(n) || n<min || n>max) throw new Error(`Valeur hors plage (${min}..${max})`);
  return n;
}
async function readNand() {
  const zone=$('nandZone').value, page=numberIn($('nandPage').value,0,131071);
  const result=await act('readNand',{zone,page});
  lastPage=result;
  $('nandSource').textContent=`Page ${page} (${zone}) · ${result.bytes.length} octets · source : ${result.source}`;
  $('nandDump').textContent=dumpHex(result.bytes,page*(zone==='main'?2048:zone==='oob'?64:1));
  return result;
}

function setDebugUi(on) {
  for(const element of document.querySelectorAll('.debug-only')) element.hidden = !on;
  if(!on) {
    const active = document.querySelector('.tab.active');
    if(active?.classList.contains('debug-only')) document.querySelector('[data-target="cpuPanel"]').click();
  }
}
$('debugMode').addEventListener('change',safe(async()=>{
  await loop.pause();
  const enabled=$('debugMode').checked;
  const result=await act('setDebug',{enabled},{record:false});
  setDebugUi(result.debugEnabled);
  log(enabled ? 'Instrumentation activée. Les traces commencent maintenant.' : 'Instrumentation désactivée. Traces libérées.');
}));

for (const tab of document.querySelectorAll('.tab')) {
  tab.addEventListener('click', () => {
    const target=tab.dataset.target;
    for(const other of document.querySelectorAll('.tab')) {
      const active=other===tab;
      other.classList.toggle('active',active);other.setAttribute('aria-selected',String(active));
    }
    for(const panel of document.querySelectorAll('section.panel')) {
      const active=panel.id===target;
      panel.classList.toggle('active',active);panel.hidden=!active;
    }
  });
}
$('backupSet').addEventListener('change',()=>{
 selectedBackupArgs=null;
 try{const result=selectBackupSet($('backupSet').files??[]);selectedBackupArgs=result.args;$('backupSelection').textContent=backupDescription(result.args)+(result.ignored.length?'\nAutres fichiers ignorés : '+result.ignored.join(', '):'');}
 catch(error){$('backupSelection').textContent=error.message;log(error.message,true);}
});
for(const id of ['flashFile','bootFile','appFile','nandFile','oobFile','eccFile'])$(id).addEventListener('change',()=>{selectedBackupArgs=null;$('backupSelection').textContent=backupDescription(fileInputs());});
$('loadFiles').addEventListener('click',safe(async()=>await loadImages(fileInputs(),'Images locales')));
$('guidedStart').addEventListener('click',safe(async()=>{
 if(busyLoading||loop.running)return;
 const args=fileInputs();
 if(args.boot||args.app)throw new Error('Le démarrage guidé utilise la Flash complète et les trois fichiers NAND. Pour des images séparées, utiliser Charger les images puis les commandes CPU.');
 selectBackupSet([args.flash,args.nand,args.oob,args.ecc].filter(Boolean));
 busyLoading=true;$('guidedStart').disabled=true;$('loadFiles').disabled=true;$('loadSample').disabled=true;$('loadAudioAlpha').disabled=true;
 $('runtimeState').textContent='Chargement local des sauvegardes et du moteur ARM…';
 try{await loadImages(args,'Sauvegardes locales');await act('reset',{mode:'boot'});guidedBoot.arm();$('runtimeState').textContent='Démarrage OEM en cours. Power sera transmis au premier sommeil du processeur.';beginContinuous();}
 finally{busyLoading=false;$('guidedStart').disabled=loop.running;$('loadFiles').disabled=loop.running;$('loadSample').disabled=loop.running;$('loadAudioAlpha').disabled=loop.running;}
}));
$('loadSample').addEventListener('click',safe(async()=>{
  const res=await fetch('./samples/board_hw_demo.bin',{cache:'no-store'});
  if (!res.ok) throw new Error('Impossible de charger le programme ARM de vérification fourni avec le site');
  const file=new File([await res.arrayBuffer()],'board_hw_demo.bin',{type:'application/octet-stream'});
  const args={flash:null,boot:null,app:file,nand:null,oob:null,ecc:null,appAddress:0x08006000};
  await loadImages(args,'Test matériel ARM original');
  await act('reset',{mode:'app'});
  log('Test ARM original chargé : exécution automatique, sans firmware AnyTone.');beginContinuous();
}));
$('resetBtn').addEventListener('click',safe(async()=>{
  guidedBoot.cancel();launchWallTime=null;await loop.pause();await act('reset',{mode:$('resetMode').value});
  log('Reset du coeur Thumb effectue; NAND overlay conserve.');
}));
$('stepBtn').addEventListener('click',safe(async()=>{
  await loop.pause();await act('step');
  log(`Pas à pas : ${hex(status.cpu.pc)}${status.cpu.stop?' · '+status.cpu.stop.category:''}`);
}));
$('runBtn').addEventListener('click',safe(async()=>{
  await loop.pause();
  const budget=numberIn($('budget').value,1,1000000), breakpoint=status?.debugEnabled ? $('breakpoint').value.trim() : '';
  await act('run',{budget,breakpoint:breakpoint||null});
  const cpu=status.cpu, reason=cpu.stop;
  log(reason
    ? `Arret ${reason.category} | PC ${hex(reason.pc??cpu.pc)} | ${reason.reason}${reason.fault?` | acces ${hex(reason.fault.address)}`:''}`
    : `Execution: budget ${cpu.lastBudget??budget} instructions | observations CPU ${status.debugEnabled?(cpu.count??0):'desactive (mode rapide)'}`,
    !!reason);
}));
$('readMemory').addEventListener('click',safe(async()=>{
  const address=parseAddress($('memoryAddress').value,0x20000000), length=numberIn($('memoryLength').value,1,256);
  const value=await act('readMemory',{address,length});
  $('memoryDump').textContent=dumpHex(value.bytes,value.address);
  log(`Memoire inspectee : ${hex(address)}, ${length} octets`);
}));
$('nandRead').addEventListener('click',safe(async()=>await readNand()));
$('downloadPage').addEventListener('click',safe(async()=>{
  const zone=$('nandZone').value,page=numberIn($('nandPage').value,0,131071);
  if(!lastPage || lastPage.page!==page || lastPage.zone!==zone) await readNand();
  saveBlob(new Blob([Uint8Array.from(lastPage.bytes)],{type:'application/octet-stream'}),`nand_${zone}_page_${page}.bin`);
}));
$('nandProgram').addEventListener('click',safe(async()=>{
  const zone=$('nandZone').value, page=numberIn($('nandPage').value,0,131071);
  const offset=numberIn($('nandOffset').value,0,2047), bytes=parseHexBytes($('nandHex').value);
  await act('programNand',{zone,page,offset,bytes});
  await readNand();
  log(`NAND overlay programmee : ${zone}, page ${page}, ${bytes.length} octets a +${offset}`);
}));
$('nandErase').addEventListener('click',safe(async()=>{
  const block=numberIn($('nandBlock').value,0,2047);
  if(!confirm(`Effacer virtuellement les pages du bloc ${block} (main et OOB) ? Les originaux restent intacts.`))return;
  await act('eraseNand',{block});
  lastPage=null;
  log(`Bloc ${block} efface dans l'overlay volatil (idealise).`);
}));
$('hashBtn').addEventListener('click',safe(async()=>{
  const role=$('hashRole').value;
  $('hashProgress').textContent=`SHA-256 ${role} : calcul en cours localement.`;
  const result=await act('hash',{role},{record:false});
  $('hashProgress').textContent=`${role} · ${result.sha256}`;
  refresh(await send('status'));
  log(`Empreinte SHA-256 ${role} calculee sans televersement.`);
}));
$('exportReport').addEventListener('click',safe(async()=>{
  const report=await act('report',{includeTrace:!!status.debugEnabled},{record:false});
  saveJson(report,'opend578-report.json');
  log('Rapport exporte sans image binaire.');
}));
$('exportScenario').addEventListener('click',safe(async()=>{
  await loop.pause();
  if(scenarioTruncated)throw new Error('Le scénario dépasse 20 000 actions. Exporter le diagnostic ou recharger les images.');
  if(!status) throw new Error('Charger une configuration avant d’exporter un scénario');
  saveJson({
    schema:'opend578.browser-scenario.v1',engine:status.engine,
    warning:'Ne contient pas les fichiers originaux; recharger ses propres images avant le replay.',
    images:status.files,appAddress:attachedArgs?.appAddress??null,actions:recordedActions
  },'opend578-scenario.json');
  log(`${recordedActions.length} action(s) enregistree(s) dans le scenario.`);
}));
$('exportNandPatch').addEventListener('click',safe(async()=>{
  guidedBoot.cancel();await loop.pause();
  $('runtimeState').textContent='Calcul des empreintes des sauvegardes et export du correctif NAND…';
  const patch=await act('exportPatch',{}, {record:false});
  if(!confirm('Le correctif peut contenir des donnees derivees de vos sauvegardes. Verifier avant de le partager. Exporter ?')){$('runtimeState').textContent='Export annulé. La session est en pause.';return;}
  saveJson(patch,'opend578-nand-overlay.json');
  $('runtimeState').textContent='Correctif exporté avec les empreintes des sauvegardes. La session est en pause.';
  log(`${patch.changes.length} page(s) exportee(s) en correctif JSON.`);
}));
async function readJson(file,limit = 15000000) {
  if(!file || file.size>limit) throw new Error('Fichier JSON manquant ou trop volumineux');
  return JSON.parse(await file.text());
}
$('importPatch').addEventListener('change',safe(async()=>{
  guidedBoot.cancel();await loop.pause();
  const patch=await readJson(fileFor('importPatch'));
  $('runtimeState').textContent='Vérification des sauvegardes avant reprise du correctif…';
  const r=await act('importPatch',{patch},{record:false});
  lastPage=null;lastLcdWrites=-1;launchWallTime=null;
  if(status.selectedVector===0x08000000)guidedBoot.arm();beginContinuous();
  $('runtimeState').textContent='Correctif vérifié et importé. Redémarrage du firmware sur les pages conservées.';
  log(`${r.importedPages} pages importées après vérification SHA-256 ; reset matériel du MCU.`);
}));
$('importScenario').addEventListener('change',safe(async()=>{
  const json=await readJson(fileFor('importScenario'),1048576);
  const allowed=TRACKED;
  if(json?.schema!=='opend578.browser-scenario.v1'||!Array.isArray(json.actions)||json.actions.length>20000||
     json.actions.some(a=>!allowed.has(a?.command)||typeof a.args!=='object'||a.args===null)) throw new Error('Format scenario non pris en charge');
  importedScenario=json;
  $('replayScenario').disabled=false;
  log(`Scenario importe : ${json.actions.length} actions (fichiers binaires non inclus).`);
}));
$('replayScenario').addEventListener('click',safe(async()=>{
  await loop.pause();
  if(!attachedArgs||!importedScenario) throw new Error('Recharger les images correspondant au scénario');
  if(importedScenario.appAddress!==null && importedScenario.appAddress!==attachedArgs.appAddress) throw new Error('Adresse application differente du scenario');
  const expected=importedScenario.images || {};
  for(const role of ['flash','boot','app','nand','oob','ecc']){
    const a=expected[role], f=attachedArgs[role];
    if(Boolean(a)!==Boolean(f)) throw new Error(`${role}: presence differente du scenario`);
    if(a && (a.size!==f.size || a.name!==f.name)) throw new Error(`${role}: nom ou taille differente`);
    if(a?.sha256 && status?.files?.[role]?.sha256 !== a.sha256){
      const value=await send('hash',{role});
      if(value.sha256!==a.sha256) throw new Error(`${role}: SHA-256 different, replay refuse`);
    }
  }
  if(!confirm(`Recharger les images et rejouer ${importedScenario.actions.length} actions sur une session vierge ?`))return;
  const actions=importedScenario.actions.slice();
  await loadImages(attachedArgs,'Reinitialisation avant replay');
  for (const item of actions) {
    await act(item.command,item.args);
  }
  log(`Replay termine : ${actions.length} actions. Verifier categorie d'arret et rapport.`);
}));
$('clearEvents').addEventListener('click',()=>$('events').replaceChildren());

(async()=>{
  setDebugUi(false);
  try { const v=await send('version'); if(v.build!=='web0151r5')throw new Error(`Worker different de la page: ${v.build??'inconnu'} (attendu web0151r5). Recharger avec Ctrl+Maj+R.`); refresh(await send('status'));$('runtimeState').textContent='Moteur Web prêt. Sélectionner les quatre sauvegardes, puis Charger et démarrer.';for(const id of ['guidedStart','loadFiles','loadSample','loadAudioAlpha'])$(id).disabled=false; log('Version Web '+v.build+' / moteur '+v.engine+' prête.'); }
  catch(error) { $('runtimeState').textContent='Démarrage impossible : '+error.message;$('runtimeState').classList.add('error');log('Demarrage impossible : '+error.message,true); }
})();

// Physical board controls. They never write OEM SRAM, LCD pixels or virtual codeplug.
const boardButtons=document.querySelectorAll('[data-hwkey]');
const heldPanel=new Map();
function resumeWaiting(wasWaiting){if(wasWaiting&&!loop.running)void loop.start(numberIn($('budget').value,1,1000000)).catch(e=>log(e.message,true));}
async function panelInput(button,down){
 const name=button.dataset.hwkey;if(!!heldPanel.get(name)===down)return;
 heldPanel.set(name,down);button.classList.toggle('pressed',down);
 const wasWaiting=status?.cpu?.stop?.category==='waiting';
 try{refresh(await act('panelKey',{name,down,minimumMs:name==='POWER'?2000:Number($('keyDuration').value)}));resumeWaiting(wasWaiting);}
 catch(e){heldPanel.set(name,false);button.classList.remove('pressed');log(e.message,true);}
}
for(const b of boardButtons){
 b.addEventListener('pointerdown',e=>{e.preventDefault();b.setPointerCapture(e.pointerId);void panelInput(b,true);});
 for(const ev of ['pointerup','pointercancel','lostpointercapture'])b.addEventListener(ev,()=>void panelInput(b,false));
 b.addEventListener('keydown',e=>{if([' ','Enter'].includes(e.key)){e.preventDefault();if(!e.repeat)void panelInput(b,true);}});
 b.addEventListener('keyup',e=>{if([' ','Enter'].includes(e.key)){e.preventDefault();void panelInput(b,false);}});
 b.addEventListener('blur',()=>void panelInput(b,false));
 b.addEventListener('click',e=>{if(e.detail===0&&!heldPanel.get(b.dataset.hwkey)){void panelInput(b,true);void panelInput(b,false);}});
}
window.addEventListener('blur',()=>{for(const b of boardButtons)void panelInput(b,false);});
const dial=document.querySelector('[data-hwkey="DIAL_PRESS"]');
dial?.addEventListener('wheel',e=>{e.preventDefault();act('boardRotate',{direction:e.deltaY<0?'up':'down'}).then(refresh).catch(e=>log(e.message,true));},{passive:false});
for(const [id,direction] of [['dialUp','up'],['dialDown','down']])$(id)?.addEventListener('click',safe(async()=>refresh(await act('boardRotate',{direction}))));
const volumePending={A:0,B:0};
async function inputVolume(which,value){volumePending[which]++;try{refresh(await act('boardVolume',{which,value}));}finally{volumePending[which]--;if(!volumePending[which]&&status?.FACADE)renderPanel(status.FACADE);}}
for(const [id,which] of [['volA','A'],['volB','B']])$(id)?.addEventListener('input',safe(async()=>inputVolume(which,Number($(id).value))));
const micHeld=new Set();
async function micInput(name,down){
 if(!status?.started)return;
 const waiting=status?.cpu?.stop?.category==='waiting';
 if(down){if(micHeld.has(name))return;micHeld.add(name);}else{if(!micHeld.delete(name))return;}
 try{const r=await act('micKey',name==='PTT'?{ptt:down}:{name,active:down});refresh({...status,board:r.board});resumeWaiting(waiting);}catch(e){if(down)micHeld.delete(name);throw e;}
}
function bindMicButton(button,name){
 button.style.touchAction='none';
 button.addEventListener('pointerdown',e=>{if(e.button!==0)return;e.preventDefault();button.setPointerCapture(e.pointerId);void safe(()=>micInput(name,true))();});
 for(const event of ['pointerup','pointercancel','lostpointercapture'])button.addEventListener(event,()=>void safe(()=>micInput(name,false))());
 button.addEventListener('keydown',e=>{if(![' ','Enter'].includes(e.key))return;e.preventDefault();if(!e.repeat)void safe(()=>micInput(name,true))();});
 button.addEventListener('keyup',e=>{if([' ','Enter'].includes(e.key)){e.preventDefault();void safe(()=>micInput(name,false))();}});
 button.addEventListener('blur',()=>void safe(()=>micInput(name,false))());
 // Assistive-technology activation has no pointer/key pair.
 button.addEventListener('click',e=>{if(e.detail===0&&!micHeld.has(name))void safe(async()=>{await micInput(name,true);await micInput(name,false);})();});
}
for(const name of [...'0123456789','*','#','SUB A/B','UP','DOWN','A','B','C','D']){const b=document.createElement('button');b.textContent=name;b.className='secondary';bindMicButton(b,name);$('wiredMicKeys').append(b);}
bindMicButton($('micPtt'),'PTT');
async function releaseMic(){micHeld.clear();if(status?.started){const waiting=status.cpu?.stop?.category==='waiting';refresh(await act('micReleaseAll'));resumeWaiting(waiting);}}
$('micRelease').addEventListener('click',safe(releaseMic));
$('micRfApply').addEventListener('click',safe(async()=>{const waiting=status?.cpu?.stop?.category==='waiting';refresh(await act('rfInputs',{bank:Number($('micRfBank').value),registers:Object.fromEntries([12,96,97,101,103].map(a=>[a,Number($('micRf'+a).value)]))}));resumeWaiting(waiting);}));
window.addEventListener('blur',()=>void safe(releaseMic)());
document.addEventListener('visibilitychange',()=>{if(document.hidden)void safe(releaseMic)();});
for(const id of ['micConnected','micLocked','micLongMs'])$(id).addEventListener('change',safe(async()=>{if(!status?.started)return;if(!$('micConnected').checked)micHeld.clear();const waiting=status.cpu?.stop?.category==='waiting';refresh(await act('micConfigure',{connected:$('micConnected').checked,locked:$('micLocked').checked,longMs:Number($('micLongMs').value)}));resumeWaiting(waiting);}));
$('gpsInject')?.addEventListener('click',safe(async()=>{await act('gpsInject',{sentence:$('nmeaSentence').value});log('GPS : trame manuelle planifiée sur le fil USART1 RX.');}));
function renderMic(mic){const v=microphoneView(mic);if(document.activeElement!==$('micLongMs'))$('micLongMs').value=String(mic?.longThresholdMs??800);$('micState').textContent=v.text;$('micConnected').checked=v.connected;$('micLocked').checked=v.locked;
 for(const lane of ['A','B'])for(const [colour,label]of [['green','RX'],['red','TX']]){const e=$('mic'+lane+(colour==='green'?'Green':'Red')),l=v[lane];e.textContent=label+' '+(l.known?(l[colour]?'ON':'OFF'):'?');e.classList.toggle('on-'+colour,l.known&&l[colour]);}
 for(const lane of ['A','B']){const e=$('micMain'+lane),on=v['main'+lane];e.textContent='MAIN '+(on===null?'?':on?'ON':'OFF');e.classList.toggle('on-white',on===true);}
 for(const b of $('wiredMicKeys').children)b.disabled=!status?.started||!v.connected||(v.locked&&['UP','DOWN'].includes(b.textContent))||(v.heldKey!==null&&v.heldKey!==b.textContent);$('micPtt').disabled=!status?.started||!v.connected;
}
let lastLcdWrites=-1;
function renderBoard(board){
  if(!board)return;
  const green=$('greenLamp'),red=$('redLamp');green.textContent='RX : '+(board.ledRaw===null?'?':board.green?'ON':'OFF');red.textContent='TX : '+(board.ledRaw===null?'?':board.red?'ON':'OFF');
  green.classList.toggle('on-green',!!board.green);red.classList.toggle('on-red',!!board.red);
  $('backlightLamp').textContent='Retro LCD DA1 : '+(board.backlightKnown?Math.round(board.backlightRaw/255*100)+'% (commande)':'?');
  $('whiteLamp').textContent='Autres sorties : '+Object.entries(board.lighting).filter(([a])=>a!=='8').map(([a,v])=>a+':'+v).join(' ');
  renderMic(board.mic);
  const revision=JSON.stringify([board.lcd?.writes,board.lcd?.displayOn,board.lcd?.sleep,board.backlightRaw]);
  if(revision!==lastLcdWrites){lastLcdWrites=revision;send('lcd').then(renderLcd).catch(()=>{});}
}
function renderLcd(model){
  const canvas=$('realLcd');if(!canvas)return;const ctx=canvas.getContext('2d',{alpha:false});
  ctx.fillStyle='#000';ctx.fillRect(0,0,160,128);
  if(!model||!model.displayOn||model.sleep||model.backlight===0)return;
  const pix=model.pixels||[],image=ctx.createImageData(160,128);
  image.data.set(landscapePixels(model));
  ctx.putImageData(image,0,0);
}
renderLcd(null);

for(const hotspot of document.querySelectorAll('button[data-volume]')){
  hotspot.addEventListener('wheel',e=>{
    e.preventDefault();const which=hotspot.dataset.volume,slider=$(which==='A'?'volA':'volB');
    const next=Math.max(0,Math.min(4095,Number(slider.value)+(e.deltaY<0?128:-128)));
    slider.value=String(next);
    inputVolume(which,next).catch(error=>log(error.message,true));
  },{passive:false});
}

$('startContinuous').addEventListener('click',safe(async()=>{
 if(!status?.started)throw new Error('Charger les images et effectuer Reset.');
 if(status.cpu.stop&&!['waiting','control'].includes(status.cpu.stop.category))throw new Error('Le moteur est arrêté. Effectuer Reset avant de reprendre.');
 await loop.start(numberIn($('budget').value,1,1000000));
}));
$('pauseContinuous').addEventListener('click',safe(async()=>{guidedBoot.cancel();await loop.pause();refresh(await send('status'));log('Exécution en pause, état du processeur conservé.');}));
$('reportQuick').addEventListener('click',safe(async()=>{
 await loop.pause();const report=await send('report',{includeTrace:!!status?.debugEnabled});
 report.scenarioTruncated=scenarioTruncated;
 saveJson(report,'opend578-diagnostic-web0151r5.json');log('Diagnostic exporté.');
}));

$('powerPulse').addEventListener('click',safe(async()=>{guidedBoot.cancel();await act('powerPulse');if(!loop.running)beginContinuous();log('PA0 maintenu à 0 pendant 2 secondes du temps du banc, puis relâché automatiquement.');}));

$('usbConnect').addEventListener('click',safe(async()=>{await act('usbConnect');if(!loop.running)void loop.start(numberIn($('budget').value,1,1000000));}));
$('usbDisconnect').addEventListener('click',safe(async()=>{await act('usbDisconnect');}));
$('cpsRead').addEventListener('click',safe(async()=>{await act('cpsRead',{address:parseAddress($('cpsAddress').value),length:numberIn($('cpsLength').value,16,4096)});if(!loop.running)void loop.start(numberIn($('budget').value,1,1000000));}));
for(const [id,command] of [['cpsRename','cpsRename'],['cpsVerify','cpsVerify'],['cpsRestore','cpsRestore']])$(id).addEventListener('click',safe(async()=>{await act(command,command==='cpsRename'?{name:$('cpsChannelName').value}:{});if(!loop.running)void loop.start(numberIn($('budget').value,1,1000000));}));
$('cpsBackup').addEventListener('click',safe(async()=>{const bytes=await send('cpsBackup');saveBlob(new Blob([bytes],{type:'application/octet-stream'}),'opend578-bloc-canaux-original.bin');}));
$('cpsExport').addEventListener('click',safe(async()=>{const bytes=await send('cpsReadBytes');saveBlob(new Blob([bytes],{type:'application/octet-stream'}),'opend578-lecture-cps.bin');}));
async function applyGps(){const wasWaiting=status?.cpu?.stop?.category==='waiting';await act('gpsScenario',{config:{mode:$('gpsMode').value,latitude:Number($('gpsLatitude').value),longitude:Number($('gpsLongitude').value),utc:$('gpsUtc').value,hertz:Number($('gpsHz').value),motion:$('gpsMotion').value,speedKmh:Number($('gpsSpeed').value),course:Number($('gpsCourse').value),sideMeters:Number($('gpsSide').value),durationSeconds:Number($('gpsDuration').value),startDelaySeconds:Number($('gpsDelay').value),talker:$('gpsTalker').value,baud:Number($('gpsBaud').value),fault:$('gpsFault').value,faultEvery:Number($('gpsFaultEvery').value)}});resumeWaiting(wasWaiting);log('Entrée GNSS appliquée sur le fil USART1 RX.');}
$('gpsApply').addEventListener('click',safe(applyGps));
$('gpsPreset').addEventListener('click',safe(async()=>{for(const [id,value] of Object.entries({gpsMode:'fix',gpsMotion:'square',gpsSpeed:36,gpsSide:30,gpsDelay:6,gpsHz:1,gpsTalker:'GP',gpsBaud:9600,gpsFault:'none',gpsFaultEvery:0}))$(id).value=value;await applyGps();}));
function renderPanel(p){$('serviceChord').textContent=p.heldKeys.includes('P4')&&p.heldKeys.includes('DIAL_PRESS')?'Relâcher P4 + appui codeur':'Maintenir P4 + appui codeur';$('audioState').textContent=audioStatusText(p.audio)+'\n\n'+audioControlText(p.audio.logicalControl);for(const v of p.volumes){const slider=$(v.name==='A'?'volA':'volB');if(!volumePending[v.name])slider.value=String(v.inputRaw);}$('panelState').textContent=p.volumes.map(v=>`Pot ${v.name} → ADC${v.ADCchannel} : entrée ${v.inputRaw} · acquis DMA ${v.acquiredRaw??'en attente'} · gain RF banque ${v.receiverBank} / 0x44 : ${v.receiverGainRaw===null?'non écrit':'0x'+v.receiverGainRaw.toString(16).padStart(4,'0')}`).join('\n')+`\nTouches maintenues : ${p.heldKeys.join(', ')||'aucune'} · ADC8 / ADC9 : ${p.analogKeys.ADC8} / ${p.analogKeys.ADC9}\nSorties PA7 / RF banque 1 reg. 0x25 bit 4 : ${p.audio.radioSpeakerMuteCandidate??'?'} / ${p.audio.microphoneSpeakerMuteCandidate??'?'} · PCM : non porté`;}
function renderGps(g){const p=g.lastSample;
 $('gpsState').textContent=`Source ${g.mode} · ${g.frames} salves · ${g.bytes} octets · ${g.baud??9600} baud · ${g.hertz} Hz demandés`+`\nCadence effective : ${1000/(g.effectiveIntervalMs??1000/g.hertz)} Hz · commandes OEM appliquées : ${g.moduleControl?.accepted??0} · rejetées : ${g.moduleControl?.rejected??0}`+(p?`\n${p.utc} · ${p.phase} · ${p.latitude.toFixed(6)}, ${p.longitude.toFixed(6)}\nVitesse d’entrée ${p.speedKmh.toFixed(2)} km/h (${(p.speedKmh/1.852).toFixed(2)} kn) · cap ${p.course.toFixed(2)}°${p.corrupted?' · salve altérée':''}`:'')+`\nSalves altérées : ${g.corruptedFrames??0} · échéances source manquées : ${g.missedPeriods??0} · fix OEM à lire sur son écran`;
 const points=g.route?.points??[];if(!points.length){$('gpsPath').setAttribute('d','');$('gpsMarker').setAttribute('visibility','hidden');return;}
 const lat0=points[0].latitude,lon0=points[0].longitude,cos=Math.cos(lat0*Math.PI/180),xy=q=>[(((q.longitude-lon0+540)%360)-180)*cos,-(q.latitude-lat0)],coords=points.map(xy),xs=coords.map(q=>q[0]),ys=coords.map(q=>q[1]),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),scale=Math.min(270/Math.max(maxX-minX,1e-7),125/Math.max(maxY-minY,1e-7)),project=q=>{const [x,y]=xy(q);return[160+(x-(minX+maxX)/2)*scale,100+(y-(minY+maxY)/2)*scale];};
 $('gpsPath').setAttribute('d',points.map((q,i)=>(i?'L':'M')+project(q).join(',')).join(' '));const q=project(p??points[0]);$('gpsMarker').setAttribute('cx',q[0]);$('gpsMarker').setAttribute('cy',q[1]);$('gpsMarker').setAttribute('visibility','visible');
}

$('sensorApply').addEventListener('click',safe(async()=>{await act('sensorInputs',{values:{6:Number($('sensor6').value),10:Number($('sensor10').value),11:Number($('sensor11').value)}});log('Mesures ADC externes appliquées.');}));


$('antennaApply').addEventListener('click',safe(async()=>{const sentence=antennaFrame($('antennaState').value),waiting=status?.cpu?.stop?.category==='waiting';refresh(await act('gpsInject',{sentence,baud:9600}));resumeWaiting(waiting);log('Événement d’antenne ATGM336H-5N transmis sur le fil UART, à 9600 baud.');}));

$('serviceChord').addEventListener('click',safe(async()=>{const keys=status?.FACADE?.heldKeys??[],down=!(keys.includes('P4')&&keys.includes('DIAL_PRESS'));await act('boardKey',{name:'P4',down});refresh(await act('boardKey',{name:'DIAL_PRESS',down}));log(down?'P4 et appui du codeur maintenus sur leurs entrées physiques.':'P4 et appui du codeur relâchés.');}));

$('audioLoad').addEventListener('click',safe(async()=>{const file=$('audioWav').files[0];if(!file)throw Error('Choisir un WAV PCM16');if(file.size>10000000)throw Error('WAV trop volumineux');const config=wavToAdcCodes(await file.arrayBuffer(),{bias:Number($('audioBias').value),amplitude:Number($('audioAmplitude').value)});refresh(await act('audioInput',{config}));log('Source externe appliquée sur PC0 / ADC10 ; aucune écriture directe SRAM.');}));
$('audioStop').addEventListener('click',safe(async()=>refresh(await act('audioInput',{config:null}))));
$('audioCapture').addEventListener('click',safe(async()=>{const data=await act('audioInputCapture');const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='OpenD578_ADC10_acquisitions.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}));

let volumeAudioUrl=null;
$('volumePcmLoad').addEventListener('click',safe(async()=>{const f=$('volumeWav').files[0];if(!f||f.size>10000000)throw Error('Choisir un WAV PCM16, 12 secondes maximum');const w=decodePcm16Wav(await f.arrayBuffer());const channels=w.channels.map((samples,i)=>({port:w.channels.length===1?Number($('volumePort').value):i+1,samples}));refresh(await act('volumePcmInput',{config:{channels,sampleRate:w.sampleRate}}));}));
$('volumePcmStop').addEventListener('click',safe(async()=>refresh(await act('volumePcmInput',{config:null}))));
$('volumePcmExport').addEventListener('click',safe(async()=>{const c=await act('volumePcmCapture');const wav=pcm16Wav(c.channels.map(x=>x.samples),c.sampleRate);if(volumeAudioUrl)URL.revokeObjectURL(volumeAudioUrl);volumeAudioUrl=URL.createObjectURL(new Blob([wav],{type:'audio/wav'}));$('volumePcmPlayer').src=volumeAudioUrl;const a=document.createElement('a');a.href=volumeAudioUrl;a.download='OpenD578_U2429_OUT'+c.channels.map(x=>x.port).join('_')+'.wav';a.click();}));

$('loadAudioAlpha').addEventListener('click',safe(async()=>{
 if(busyLoading||loop.running)return;busyLoading=true;$('loadAudioAlpha').disabled=true;
 try{const res=await fetch('./samples/audio_alpha.bin',{cache:'no-store'});if(!res.ok)throw Error('Programme audio alpha introuvable');const file=new File([await res.arrayBuffer()],'audio_alpha.bin',{type:'application/octet-stream'});await loadImages({flash:null,boot:null,app:file,nand:null,oob:null,ecc:null,appAddress:0x08006000},'Programme audio indépendant, RF non initialisée');await act('reset',{mode:'app'});guidedBoot.cancel();log('Audio alpha : potentiomètres A/B, P1 mute A, P4 mute B, MENU coupe, EXIT rouvre. Pas de réception RF.');beginContinuous();}finally{busyLoading=false;$('loadAudioAlpha').disabled=loop.running;}
}));
