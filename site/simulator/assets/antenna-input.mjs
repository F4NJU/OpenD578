/* ATGM336H-5N manual §2.8: UART messages on antenna-state changes.
 * Explicit external input only. Exact installed module variant is not inferred.
 * https://icofchina.com/d/file/xiazai/2020-09-22/35258a39d8050a9a32ade72ef103c8b5.pdf */
import {nmea} from './gps-input.mjs?build=web0160r1';
export function antennaFrame(state){const labels={ok:'OK',open:'OPEN',short:'SHORT'};if(!Object.hasOwn(labels,state))throw Error('Choisir un état d’antenne ATGM336H-5N');return nmea('GPTXT,01,01,01,ANTENNA '+labels[state]);}
