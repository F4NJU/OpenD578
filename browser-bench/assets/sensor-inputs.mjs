/* Physical ADC stimuli and passive hardware observations. No OEM SRAM/PC ABI.
 * SWR detector routing is deliberately unassigned until established. */
export const SENSOR_CHANNELS=Object.freeze([6,10,11]);
export function setSensorInputs(board,values){
 if(!values||typeof values!=='object'||Array.isArray(values)||!Object.keys(values).length)throw Error('Mesures ADC absentes');
 const entries=Object.entries(values);
 if(board.audioInput?.config&&Object.hasOwn(values,"10"))throw Error("Arrêter la source audio ADC10 avant une mesure statique");
 for(const [key,value] of entries)if(!SENSOR_CHANNELS.map(String).includes(key)||!Number.isInteger(value)||value<0||value>4095)throw Error('Entrées capteurs : ADC6/10/11, entiers 0..4095');
 for(const [key,value] of entries)board.adc.set(Number(key),value);
}
export function sensorStatus(board,hardware){
 const fan=hardware?.rf.regs.get('0:0:37');
 return {adc:Object.fromEntries(SENSOR_CHANNELS.map(c=>[c,board.adc.get(c)])),
  dac0:hardware?.dac[0x42c]??null,dac1:hardware?.dac[0x430]??null,
  fanRegister:fan??null,fanBit:fan===undefined?null:!!(fan&2),
  swr:{qualified:false,measurementRoute:null,threshold:null,reason:'Mesure, seuil et réaction SWR/ROS OEM non identifiés'},
  source:'External raw ADC test inputs; DAC and RF register observations only',directFirmwareStateWrite:false};
}
