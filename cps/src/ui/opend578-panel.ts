import { BenchHttpApi, benchOrigin } from '../device/bench-http.ts';
import { OpenD578ReadOnlyClient } from '../device/opend578-readonly.ts';
import type { OpenD578LiveSnapshot } from '../device/opend578-readonly.ts';
import { formatMHz } from '../core/frequency.ts';
const nativeDialog = document.querySelector<HTMLDialogElement>('#bench-dialog')!;
let nativeBusy = false, nativeAbort: AbortController | null = null;
let nativeSnapshot: OpenD578LiveSnapshot | null = null;
const nativeEscape = (value: string): string => value.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]!);
function nativeMessage(value: string, error = false): void {
  const element = nativeDialog.querySelector<HTMLElement>('#native-status')!;
  element.textContent = value; element.classList.toggle('error',error); element.setAttribute('role',error?'alert':'status');
}
function nativeControls(): void {
  nativeDialog.querySelectorAll<HTMLButtonElement>('#native-read,[data-native-close]').forEach(button => { button.disabled=nativeBusy; });
  nativeDialog.querySelector<HTMLButtonElement>('#native-cancel')!.disabled=!nativeBusy;
  nativeDialog.querySelector<HTMLButtonElement>('#native-export')!.disabled=nativeBusy||!nativeSnapshot;
}
async function readNativeVfos(): Promise<void> {
  if(nativeBusy)return;nativeBusy=true;nativeAbort=new AbortController();nativeSnapshot=null;nativeControls();
  nativeDialog.querySelector('#native-results')!.replaceChildren();nativeMessage('Identification OpenD578 puis lecture des deux VFO.');
  try {
    const transport=new BenchHttpApi({protocol:'opend578-ro',signal:nativeAbort.signal});await transport.initialize();
    nativeSnapshot=await new OpenD578ReadOnlyClient((path,data)=>transport.request(path,data),{signal:nativeAbort.signal}).readVfos();
    const snapshot=nativeSnapshot;
    nativeDialog.querySelector('#native-results')!.innerHTML=`<p>Firmware : <strong>${nativeEscape(snapshot.firmware)}</strong> · VFO sélectionné : ${snapshot.selected}</p>
      <div class="table-scroll"><table aria-label="VFO du firmware OpenD578"><thead><tr><th>VFO</th><th>RX · MHz</th><th>Largeur</th><th>Émission</th></tr></thead><tbody>${snapshot.vfos.map(vfo=>`<tr><td>${vfo.id}</td><td>${formatMHz(vfo.rxHz)}</td><td>${vfo.bandwidth==='narrow'?'Étroite':'Large'}</td><td>Inhibée</td></tr>`).join('')}</tbody></table></div>
      <p class="help">Fonctions annoncées par ce firmware :</p><ul>${Object.entries(snapshot.capabilities).map(([key,value])=>`<li>${nativeEscape(({vfoRead:'Lecture des VFO',vfoWrite:'Modification des VFO',memories:'Mémoires de canaux',ctcss:'CTCSS',dcs:'DCS',tx:'Émission',persistent:'Sauvegarde persistante'} as Record<string,string>)[key])} : ${value?'oui':'non'}</li>`).join('')}</ul>
      <p class="help">Lecture des valeurs du firmware neuf. Aucun canal du document n'est remplacé et aucune fonction du firmware constructeur n'est utilisée.</p>`;
    nativeMessage('Lecture terminée. Vous pouvez relire après une action sur le codeur du banc, sans terminer ni redémarrer une session CPS.');
  }catch(error){nativeMessage(nativeAbort.signal.aborted?'Lecture interrompue.':(error as Error).message,true);}
  finally{nativeBusy=false;nativeAbort=null;nativeControls();}
}
export function openOpenD578Panel(): void {
  let connected=false;try{connected=location.pathname.startsWith('/cps/')&&benchOrigin(location.origin)===location.origin;}catch{}
  nativeDialog.innerHTML=`<div class="dialog-head"><h2 id="bench-title">OpenD578 · firmware neuf · VFO en lecture seule</h2><button data-native-close aria-label="Fermer">×</button></div>
    <div class="dialog-body"><p>Ce panneau utilise le protocole OpenD578 de l'alpha RX FM avec extension CPS. Il est distinct du panneau OEM.</p>
    <p class="help">Dans le banc Python : modèle Matériel, NAND vierge, fichier rx_fm_cps.bin, démarrage application, moteur natif. Le binaire de banc ne doit pas être envoyé au poste physique.</p>
    ${connected?`<div class="actions"><button id="native-read" class="primary">Identifier et lire A/B</button><button id="native-cancel" disabled>Interrompre</button><button id="native-export" disabled>Exporter l'observation</button></div>`:`<p>Ouvrez ce CPS depuis l'adresse du banc, par exemple <a href="http://127.0.0.1:8765/cps/" target="_blank" rel="noopener noreferrer">http://127.0.0.1:8765/cps/</a>.</p>`}
    <div id="native-status" class="notice" role="status">Attendre le démarrage de l'alpha. Aucun réglage ni mémoire n'est écrit.</div><div id="native-results"></div></div>
    <div class="dialog-footer"><button data-native-close>Fermer</button></div>`;
  nativeDialog.querySelectorAll('[data-native-close]').forEach(button=>button.addEventListener('click',()=>nativeDialog.close()));
  if(connected){
    nativeDialog.querySelector('#native-read')!.addEventListener('click',()=>{void readNativeVfos();});
    nativeDialog.querySelector('#native-cancel')!.addEventListener('click',()=>nativeAbort?.abort());
    nativeDialog.querySelector('#native-export')!.addEventListener('click',()=>{
      if(!nativeSnapshot)return;const url=URL.createObjectURL(new Blob([JSON.stringify(nativeSnapshot,null,2)],{type:'application/json'}));
      const link=document.createElement('a');link.href=url;link.download='OpenD578-VFO-observation.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
  }
  nativeDialog.showModal();
}
nativeDialog.addEventListener('cancel',event=>{if(nativeBusy){event.preventDefault();nativeAbort?.abort();}});
window.addEventListener('beforeunload',event=>{if(nativeBusy){event.preventDefault();event.returnValue='';}});
