/* Passive reference-OEM frequency command pairs. QA address meanings are
 * recovered from OEM 0806E100/0806E380 and actual V1.21 traces, not AT1846S. */
import {REFERENCE_FLASH_SHA} from './calibration-status.mjs?build=web0160r1';
export class RfFrequencyCommands {
 constructor(){this.pending=[null,null,null,null];this.committed=[null,null,null,null];this.pairs=0;}
 observe(f){
  if(!f||f.bank<0||f.bank>3)return;
  const b=f.bank;
  if(!f.read&&f.page===0&&f.register===0x38){this.pending[b]={low:f.value,sequence:f.sequence,time:f.time};return;}
  if(!f.read&&f.page===0&&f.register===0x39&&this.pending[b]){
   const p=this.pending[b],word=(f.value*65536+p.low)>>>0;
   this.committed[b]={word,frequencyHz:word*10,low:p.low,high:f.value,firstSequence:p.sequence,lastSequence:f.sequence,firstTime:p.time,lastTime:f.time};this.pairs++;
  }
  this.pending[b]=null;
 }
 status(flashSha){const profileQualified=flashSha===REFERENCE_FLASH_SHA;return {profileQualified,pairs:this.pairs,source:'completed RF register 0x38 then 0x39 writes, page 0',guestStateAccess:false,banks:this.committed.map((p,bank)=>({bank,known:p!==null,pendingLowHalf:this.pending[bank]!==null,...(p??{}),frequencyHz:profileQualified?p?.frequencyHz??null:null})),physicalPLLlockMeasured:false};}
}
export function powerCalibrationStatus(provenance,flashSha){
 const qualified=flashSha===REFERENCE_FLASH_SHA;
 return {profileQualified:qualified,source:'NAND bytes actually read by OEM',activeCopyInferred:false,calibrationOverrides:false,copies:qualified?[0x2f60000,0x2f80000].map(base=>({base,bands:[{name:'UHF',baseOffset:0,curveOffset:0x200,stride:0x80,length:121},{name:'VHF',baseOffset:0x40,curveOffset:0x400,stride:0x40,length:45}].map(b=>({name:b.name,levels:Array.from({length:4},(_,level)=>({level,baseAddress:base+b.baseOffset+level+1,baseCode:provenance.observedByte(base+b.baseOffset+level+1),curveAddress:base+b.curveOffset+level*b.stride,curveLength:b.length,observedCurveBytes:Array.from({length:b.length},(_,i)=>provenance.observedByte(base+b.curveOffset+level*b.stride+i).known).filter(Boolean).length}))}))})):[]};
}
export function rfCommandText(status){
 if(!status)return 'Commandes RF en attente.';
 const f=status.frequencies,fmt=x=>x===null?'inconnue':(x/1e6).toFixed(6)+' MHz';
 const lines=['Fréquences commandées · dernières paires complètes 0x38/0x39'];
 for(const b of f.banks)lines.push(`Banque ${b.bank} : ${fmt(b.frequencyHz)}${b.pendingLowHalf?' · nouvelle paire en cours':''}`);
 lines.push(`Consigne TX DAC0 : ${status.dac0??'non reçu'} / 4095 · puissance RF en watts non mesurée`);
 if(status.calibration.profileQualified)for(const c of status.calibration.copies){const bands=c.bands.filter(b=>b.levels.some(l=>l.baseCode.known||l.observedCurveBytes));if(!bands.length)continue;lines.push(`Calibration NAND 0x${c.base.toString(16)}`);for(const b of bands)lines.push(`${b.name} · codes de base Low/Mid/High/Turbo : ${b.levels.map(l=>l.baseCode.known?l.baseCode.value:'?').join(' / ')} · tables lues : ${b.levels.map(l=>l.observedCurveBytes+'/'+l.curveLength).join(', ')}`);}
 lines.push('La sélection de voie, la fréquence et la consigne restent produites par le firmware.');return lines.join('\n');
}
