(() => {
'use strict';
const el=id=>document.getElementById(id);let features=[];
function draw(){const search=el('qualificationFilter').value.toLocaleLowerCase('fr');const body=el('qualificationRows');body.replaceChildren();
 for(const f of features.filter(f=>(f.id+' '+f.title+' '+f.acceptance).toLocaleLowerCase('fr').includes(search))){const tr=document.createElement('tr');for(const value of [f.id,f.title,f.model==='partial'?'Partiel':'Manquant',f.acceptance]){const td=document.createElement('td');td.textContent=value;tr.append(td);}body.append(tr);}}
el('qualificationFilter').oninput=draw;
api('qualification/catalog').then(c=>{features=c.features;el('qualificationSummary').textContent=features.length+' fonctions ou exigences recensées. Inventaire non exhaustif ; aucun verdict global de conformité matérielle.';draw();}).catch(e=>{el('qualificationSummary').textContent=e.message;});
function updateOutputs(){const outputs=state.hardware?.board_outputs,led=outputs?.indicators?.radio_status;
 const colours={off:'#27303a',red:'#ef4242',green:'#48dd79','red+green':'linear-gradient(90deg,#ef4242 50%,#48dd79 50%)',unknown:'#53635d'};
 el('statusLed').style.background=colours[led?.state||'unknown'];el('statusLed').style.boxShadow=led?.red||led?.green?'0 0 9px '+(led.red?'#ef4242':'#48dd79'):'none';
 el('statusLedInfo').textContent=led?.decoded?'LED : '+led.state+' · bus PE3/PE4':'LED : commande inconnue';
 el('statusLed').title='Commande série réellement émise ; couleurs inférées par corrélation firmware et observation utilisateur, continuité physique non mesurée';
 el('micOutput').textContent=outputs?JSON.stringify(outputs.microphone_output,null,2):'État électrique du microphone non disponible';if(!closed)setTimeout(updateOutputs,500);}

updateOutputs();
})();
