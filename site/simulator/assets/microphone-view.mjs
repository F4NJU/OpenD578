/* Display only completed microphone UART commands. No optimistic key-to-lamp path. */
export function microphoneView(mic={}){
 const known=mic.connected!==false&&mic.commandsValid&&mic.indicators;
 const lamps=lane=>known?{red:!!mic.indicators[lane].red,green:!!mic.indicators[lane].green,known:true}:{red:false,green:false,known:false};
 return{connected:mic.connected!==false,locked:!!mic.locked,heldKey:mic.heldKey??null,ptt:!!mic.ptt,A:lamps('A'),B:lamps('B'),mainA:known?mic.indicators.mainA:null,mainB:known?mic.indicators.mainB:null,
 text:mic.connected===false?'Microphone déconnecté':known?`Canal principal ${mic.main} · ${mic.frames} trames reçues · ${mic.singleAA??0} acquittements AA`:`Attente d’une trame complète valide${mic.error?' · '+mic.error:''}`};
}
