/* V1.21 documentary labels for bytes actually observed on the NAND wire.
 * No guest RAM reads, no audio gain injection, no writable calibration API. */
export const REFERENCE_FLASH_SHA='e2f2483baf60e2bfcab656e25e949670713222591ef4d611d6089054819a750e';
export const AUDIO_SERVICE_FIELDS=Object.freeze([
 {label:'MODU',offset:0x05,mode:18}, {label:'MIC',offset:0x19,mode:19},
 {label:'TONEU',offset:0x17,mode:20}, {label:'TONEV2',offset:0x18,mode:21},
 {label:'CTCW',offset:0x06,mode:22}, {label:'DCSW',offset:0x07,mode:23},
 {label:'MODV1',offset:0x45,mode:53}, {label:'MODV2',offset:0x57,mode:54}
]);
export function serviceCalibrationStatus(provenance,flashSha){
 const qualified=flashSha===REFERENCE_FLASH_SHA;
 return {profile:'PRO GD32 V1.21 reference image',profileQualified:qualified,units:'raw OEM codes; physical gain/deviation units unqualified',source:'NAND bytes actually clocked to the MCU',activeCopyInferred:false,calibrationOverrides:false,
  copies:qualified?[0x02f60000,0x02f80000].map(base=>({base,fields:AUDIO_SERVICE_FIELDS.map(f=>({...f,address:base+f.offset,...provenance.observedByte(base+f.offset)}))})):[]};
}
export function qaAudioStatus(rf){
 const reg=(bank,page,address)=>rf?.written.has(`${bank}:${page}:${address}`)?rf.regs.get(`${bank}:${page}:${address}`):null;
 return {source:'completed RF GPIO writes',physicalTransferQualified:false,banks:[0,1].map(bank=>{
  const select=reg(bank,0,0x18),gain=reg(bank,1,0x17);
  return {bank,register18:select,registerPage1_17:gain,microphoneSelectorRaw:select!==null&&(select&0x7ff)===0x125?select>>>11:null,microphoneAppliedCodeRaw:gain!==null&&(gain&0xfe07)===0x200?(gain>>>3)&63:null,modulationRegister40:reg(bank,0,0x40),subaudioRegister51:reg(bank,0,0x51)};
 })};
}
export function calibrationStatusText(s){
 if(!s?.profileQualified)return 'Correspondance des champs de calibration non qualifiée pour cette Flash. Les lectures NAND brutes restent disponibles.';
 const hex=n=>'0x'+n.toString(16).padStart(8,'0');
 const lines=['Réglages de service · octets effectivement lus depuis la NAND'];
 for(const c of s.copies){lines.push(`Copie ${hex(c.base)}`);for(const f of c.fields)lines.push(`${f.label} ${hex(f.address)} : ${f.known?f.value:'non lu'}`);}
 lines.push('Codes bruts propres à la sauvegarde. Aucun remplacement ni réglage en dB supposé.');
 return lines.join('\n');
}
