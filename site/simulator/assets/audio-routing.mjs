/* Logical control links from reference OEM V1.21. Passive bus/pin decoding only.
 * No MCU memory access, inferred menu state, audio source injection or PCM route.
 * GPIO/PIO identify firmware commands; unattributed physical output nets remain unknown.
 */
import {REFERENCE_FLASH_SHA} from './calibration-status.mjs?build=web0160r1';
export function audioControlStatus(board,rf,flashSha){
 const profileQualified=flashSha===REFERENCE_FLASH_SHA;
 const pio25=rf?.written.has('1:0:37')?rf.regs.get('1:0:37'):null;
 const pa7=(board.mode('A',7)&3)?!!(board.out.A&128):null;
 const bits=Object.fromEntries([0,1,2,4,5,6,7].map(n=>[n,pio25===null?null:!!(pio25&(1<<n))]));
 return {profile:'PRO GD32 V1.21 reference',profileQualified,source:'completed GPIO/RF writes',
  raw:{PA7:pa7,bank1Page0Reg25:pio25,bits},
  commands:profileQualified?{
   radioSpeakerMuted:pa7,microphoneSpeakerMuted:bits[4],
   pathSelector7:bits[7],routeGate2:bits[2],
   selectorMeaning:'standard path-apply routine: MAIN sets bit7; SUB clears bit7. Other OEM routines may override it.',
   gateMeaning:'contextual route control; not a fixed A/B selector'
  }:null,
  independentVolumeChannels:[{channel:1,DATA:'PA13',CLOCK:'PA14'},{channel:2,DATA:'PA13',CLOCK:'PA14'}],
  effectiveReceiverAtMicrophone:null,PCMConnected:false,guestStateAccess:false};
}
export function audioControlText(s){
 if(!s)return 'Commandes de routage en attente.';
 const logic=v=>v===null?'non reçu':v?'1':'0';
 const hex=s.raw.bank1Page0Reg25===null?'non reçu':'0x'+s.raw.bank1Page0Reg25.toString(16).padStart(4,'0');
 const lines=[`Routage · registre de sortie RF banque 1 / 0x25 : ${hex}`];
 if(!s.profileQualified){lines.push(`PA7 : ${logic(s.raw.PA7)} · profil des liaisons non établi pour cette Flash.`);return lines.join('\n');}
 const mute=v=>v===null?'non commandé':v?'coupure demandée':'ouverture demandée';
 lines.push(`HP poste · PA7 : ${mute(s.commands.radioSpeakerMuted)}`,
  `HP micro · PIO bit 4 : ${mute(s.commands.microphoneSpeakerMuted)}`,
  `Sélection de chemin · bit 7 : ${logic(s.commands.pathSelector7)} · porte de routage bit 2 : ${logic(s.commands.routeGate2)}`,
  'La routine de sélection applique MAIN = bit 7 à 1, SUB = bit 7 à 0. Le routage temporaire reste commandé par l’OEM.',
  'MAIN/SUB désigne un rôle ; ces bits seuls ne permettent pas de nommer la voie A/B audible.');
 return lines.join('\n');
}
