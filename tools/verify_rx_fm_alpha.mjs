/* Actual ARM-produced LCD and bus observations, no OEM SRAM hooks. */
import fs from 'node:fs';import{createRequire}from'node:module';import{WasmMachine}from'../browser-bench/assets/wasm-machine.mjs';import{landscapePixels}from'../browser-bench/assets/lcd-panel.mjs';
const root=new URL('../',import.meta.url),path=x=>new URL(x,root),lib=await createRequire(import.meta.url)('../browser-bench/vendor/unicorn_arm.js')(),m=new WasmMachine({factory:async()=>lib});
try{
 await m.attach({app:new File([fs.readFileSync(path('browser-bench/samples/rx_fm_alpha.bin'))],'rx_fm_alpha.bin')});m.reset();m.setVolume('A',4095);m.setVolume('B',1800);
 let txHigh=0;const write=m.board.write.bind(m.board);m.board.write=(...a)=>{const r=write(...a);if((m.board.out.E&64)||(m.board.out.C&16))txHigh++;return r;};
 const until=p=>{for(let i=0;i<1600;i++){const s=m.run(30000);if(s.cpu.stop&&s.cpu.stop.category!=='waiting')throw Error(s.cpu.stop.reason);if(p())return;}throw Error('RX outcome missing');};
 until(()=>m.board.lcd.writes>=20480&&m.board.volumeChip.status().channels.every(c=>c.known));
 m.core.hardware.rf.setInputs(0,{12:2,101:10,103:200});m.core.hardware.rf.setInputs(1,{12:2,101:10,103:200});
 until(()=>m.board.green&&m.board.volumeChip.status().channels.every(c=>!c.mute));
 for(let i=0;i<100;i++){const s=m.run(30000);if(s.cpu.stop&&s.cpu.stop.category!=='waiting')throw Error(s.cpu.stop.reason);}
 const rf=m.core.hardware.rf,e={program:'rx_fm_alpha',build:JSON.parse(fs.readFileSync(path('firmware/experiments/rx_fm_alpha/build.json'))),scope:'independent RX commands in ARM bench, externally supplied detector samples; no RF demodulation or hardware qualification',virtualUnits:m.core.time,RCU:m.core.boot.status(),volumeChannels:m.board.volumeChip.status().channels,lcdWrites:m.board.lcd.writes,adcTransfers:m.core.hardware.adc.total,RFtransactions:rf.total,frequencyWords:rf.frequencyCommands.committed,txGateHighObservations:txHigh,gates:{PE6:!!(m.board.out.E&64),PC4:!!(m.board.out.C&16),DAC0:m.core.hardware.dac[0x42c]??0},LEDword:m.board.ledRaw};
 if(txHigh)throw Error('TX gate rose');fs.writeFileSync(path('docs/evidence/rx_fm_alpha/boot.json'),JSON.stringify(e,null,2)+'\n');fs.writeFileSync(path('docs/evidence/rx_fm_alpha/screen.rgba'),landscapePixels(m.board.lcd.snapshot()));console.log(JSON.stringify(e));
}finally{m.core?.close();}
