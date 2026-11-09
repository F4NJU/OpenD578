import test from 'node:test';import assert from 'node:assert/strict';
import {NandSpi} from '../assets/nand-spi.mjs';import {NandReadProvenance} from '../assets/nand-provenance.mjs';
import {SctAudioControl} from '../assets/audio-devices.mjs';
import {serviceCalibrationStatus,calibrationStatusText,qaAudioStatus,REFERENCE_FLASH_SHA} from '../assets/calibration-status.mjs';
import fs from 'node:fs';import {createRequire} from 'node:module';import {WasmMachine} from '../assets/wasm-machine.mjs';
function transaction(n,bytes){n.drive(0,256);for(const b of bytes)for(let i=7;i>=0;i--){const data=((b>>i)&1)<<14;n.drive(data,0xc000);n.drive(data|0x8000,0x8000);}n.drive(256,256);}
test('NAND calibration provenance counts bytes clocked from cache, not 2048-byte prefetch; data and ECC remain unchanged',()=>{
 const observed=[],source={readPageSync(zone,row){const b=new Uint8Array(zone==='main'?2048:zone==='oob'?64:1);if(zone==='main'){b[16]=0x36;b[17]=0x55;}if(zone==='ecc')b[0]=0x20;return {bytes:b,source:'captured input'};}};
 const n=new NandSpi(source,{onRead:e=>observed.push(e)});transaction(n,[0x13,0,0,0]);assert.equal(observed.length,0);assert.equal(n.status&0x30,0x20);
 transaction(n,[3,0,16,0,0,0]);assert.deepEqual(observed.map(e=>[e.zone,e.address,e.value]),[['main',16,0x36],['main',17,0x55]]);
 assert.equal(n.outputByte(4),0x36);assert.equal(observed.length,2);assert.equal(n.status&0x30,0x20);
});
test('NAND provenance leaves unobserved regions unknown, coalesces actual byte columns, and records volatile-overlay source',()=>{
 const p=new NandReadProvenance([{name:'test region',start:0,end:2048}]);
 assert.equal(p.status().pages.length,0);p.observe({zone:'oob',address:16,page:0,column:16,value:12,source:'capture'});
 p.observe({zone:'main',address:16,page:0,column:16,value:54,source:'capture'},10);p.observe({zone:'main',address:17,page:0,column:17,value:55,source:'overlay'},20);p.observe({zone:'main',address:16,page:0,column:16,value:54,source:'capture'},30);
 const s=p.status();assert.equal(s.readBytes,3);assert.equal(s.pages[0].uniqueBytes,2);assert.deepEqual(s.pages[0].ranges,[{start:16,end:18}]);assert.deepEqual(s.pages[0].sources,['capture','overlay']);assert.equal(s.calibrationOverrides,false);assert.equal(s.directFirmwareStateWrites,false);
});
test('SCT analog calibration fields retain separate Q11/Q12 gains and do not turn automatic demod calibration into zero gain',()=>{
 const a=new SctAudioControl();assert.equal(a.status().analogConfig,null);a.field(28,[0,0]);assert.equal(a.status().demodulationGain.autoCalibration,true);assert.equal(a.status().demodulationGain.linearGain,null);
 a.field(28,[8,0]);a.field(44,[16,0]);assert.equal(a.status().demodulationGain.linearGain,1);assert.equal(a.status().modulationGain.linearGain,2);
 a.field(60,[0x8e,8,0,16,0,8,0,32,0,4,0]);const c=a.status().analogConfig;
 assert.equal(c.TXbeforeLimiter.gain,1);assert.equal(c.TXafterLimiter.gain,1);assert.equal(c.CTCSS.gain,0.5);assert.equal(c.DCS.gain,2);assert.equal(c.RXvolume.gain,0.5);assert.equal(c.IFchannelKHz,25);assert.equal(c.basebandCornerHz,3000);assert.equal(c.skipEmphasis,true);assert.equal(c.filterBypass,false);assert.equal(c.extra3kHzAttenuation,true);
});
test('factory labels only show actually consumed bytes for the qualified firmware; no nominal calibration is substituted',()=>{
 const p=new NandReadProvenance();let s=serviceCalibrationStatus(p,REFERENCE_FLASH_SHA);assert.equal(s.copies[0].fields.find(f=>f.label==='MIC').known,false);
 p.observe({zone:'main',page:0x2f60000/2048,column:0x19,address:0x2f60019,value:54,source:'captured input'},10);
 s=serviceCalibrationStatus(p,REFERENCE_FLASH_SHA);assert.equal(s.copies[0].fields.find(f=>f.label==='MIC').value,54);assert.equal(s.copies[1].fields.find(f=>f.label==='MIC').known,false);assert.equal(s.calibrationOverrides,false);assert.equal(s.activeCopyInferred,false);assert.match(calibrationStatusText(s),/MIC 0x02f60019 : 54/);
 const unknown=serviceCalibrationStatus(p,'different application');assert.equal(unknown.profileQualified,false);assert.deepEqual(unknown.copies,[]);assert.match(calibrationStatusText(unknown),/brutes restent disponibles/);
});
test('QA microphone selectors follow written bus registers, retain unknown encodings, and never interpret raw codes as dB',()=>{
 const rf={regs:new Map([['0:0:24',0x2925],['0:1:23',0x3b0],['1:1:23',0xaa8]]),written:new Set()};
 assert.equal(qaAudioStatus(rf).banks[0].microphoneAppliedCodeRaw,null);
 rf.written=new Set(rf.regs.keys());const s=qaAudioStatus(rf);assert.equal(s.banks[0].microphoneSelectorRaw,5);assert.equal(s.banks[0].microphoneAppliedCodeRaw,54);assert.equal(s.banks[1].microphoneAppliedCodeRaw,null);assert.equal(s.physicalTransferQualified,false);assert.equal(rf.regs.get('0:1:23'),0x3b0);
});
test('manual MCU reset does not present calibration bytes observed in the previous boot as newly read',async()=>{
 const lib=await createRequire(import.meta.url)('../vendor/unicorn_arm.js')(),m=new WasmMachine({factory:async()=>lib});
 await m.attach({app:new File([fs.readFileSync(new URL('../samples/board_hw_demo.bin',import.meta.url))],'board_hw_demo.bin')});
 try{m.nandProvenance.observe({zone:'main',page:0x2f60000/2048,column:25,address:0x2f60019,value:54,source:'prior capture'},100);assert.equal(m.status().NAND_PROVENANCE.readBytes,1);assert.equal(m.report().nandReadProvenance.readBytes,1);assert.equal(m.report().audioCalibration.calibrationOverrides,false);m.reset();assert.equal(m.status().NAND_PROVENANCE.readBytes,0);assert.equal(m.status().NAND_PROVENANCE.pages.length,0);}finally{m.core.close();}
});
