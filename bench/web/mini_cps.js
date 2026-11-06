(() => {
'use strict';
const el=id=>document.getElementById(id),{MiniCps,channels,rename,same,hex}=D578Cps;
let snapshot=null,pageIndex=null,busy=false,endedEngine=null;
function status(text){el('miniStatus').textContent=text;}
function buttons(){el('miniRead').disabled=busy||!!endedEngine;el('miniEnd').disabled=busy||!!endedEngine;el('miniWrite').disabled=busy||!snapshot;el('miniExport').disabled=busy||!snapshot;el('miniPage').disabled=busy;}
function render(){const body=el('miniRows');body.replaceChildren();channels(snapshot).forEach((row,i)=>{
 const tr=document.createElement('tr');
 for(const value of [pageIndex*32+i+1,null,row.rx===null?'—':(row.rx/1e6).toFixed(5),row.tx===null?'—':(row.tx/1e6).toFixed(5),['FM','DMR','FM + DMR RX','DMR + FM RX'][row.mode],['Low','Mid','High','Turbo'][row.power]]){
  const td=document.createElement('td');if(value===null){const input=document.createElement('input');input.value=row.name;input.maxLength=16;input.disabled=!row.editable;input.dataset.row=i;input.setAttribute('aria-label','Nom canal '+(pageIndex*32+i+1));td.append(input);}else td.textContent=value;tr.append(td);
 }body.append(tr);
 });}
async function run(action){if(busy)return;busy=true;buttons();const client=new MiniCps(api,(label,n,total)=>status(label+' : '+Math.round(100*n/total)+' %'));
 try{await action(client);}catch(e){if(client.mutationStarted){endedEngine=client.engine;snapshot=null;}status('Arrêt : '+e.message+' Les changements affichés ne sont pas confirmés.');}
 finally{busy=false;buttons();}}
el('miniPage').onchange=()=>{snapshot=null;el('miniRows').replaceChildren();buttons();};
el('miniRead').onclick=()=>run(async c=>{status('Connexion et identification…');await c.begin();const index=+el('miniPage').value;const data=await c.readPage(index);snapshot=data;pageIndex=index;render();status('Lecture terminée, programmation maintenue active. Les noms valides sont modifiables ; les autres champs sont en lecture seule.');});
el('miniWrite').onclick=()=>run(async c=>{
 const names={};el('miniRows').querySelectorAll('input:not(:disabled)').forEach(input=>{if(input.value!==channels(snapshot)[+input.dataset.row].name)names[input.dataset.row]=input.value;});
 const modified=rename(snapshot,names);if(same(snapshot,modified)){status('Aucun nom modifié.');return;}
 status('Identification et vérification de la page avant écriture…');await c.begin();await c.writePage(pageIndex,snapshot,modified);
 endedEngine=c.engine;snapshot=null;status('Page acquittée et END envoyé. Laisser le moteur terminer ses écritures NAND, puis arrêter et redémarrer le moteur avant de relire pour vérifier. Pour conserver après arrêt : activer la sauvegarde NAND avant le démarrage.');
});
el('miniEnd').onclick=()=>run(async c=>{await c.begin();await c.end();endedEngine=c.engine;snapshot=null;status('END envoyé. Laisser terminer le firmware puis redémarrer le moteur pour reprendre.');});
el('miniExport').onclick=()=>{const blob=new Blob([JSON.stringify({format:'OpenD578-mini-CPS-page-v1',page:pageIndex,address:'0x'+(0x800000+pageIndex*2048).toString(16),raw_hex:hex(snapshot),channels:channels(snapshot)},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='OpenD578_page_'+(pageIndex+1)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
buttons();
async function watchRestart(){if(endedEngine&&!busy){try{const s=await api('usb/cdc?view=summary');if(s.engine_instance!==endedEngine&&s.state!=='stopped'){endedEngine=null;snapshot=null;el('miniRows').replaceChildren();status('Nouveau moteur détecté. Attendre la fin du démarrage puis lire.');buttons();}}catch(e){/* Retry on next poll. */}}if(!closed)setTimeout(watchRestart,1000);}
watchRestart();
})();
