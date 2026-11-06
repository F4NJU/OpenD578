(() => {
  const el=id=>document.getElementById(id);let session=null;
  function command(){
    const port=el('cdcPort').value;
    el('cdcCommand').textContent='Windows :\n.venv\\Scripts\\python.exe cps_bridge.py --url '+location.origin+' --port '+port+' --prepare\n\nLinux :\n.venv/bin/python cps_bridge.py --url '+location.origin+' --pty';
  }
  command();el('cdcPort').oninput=command;
  el('cdcConnect').onclick=()=>api('usb/start',{}).catch(e=>note(e.message,true));
  el('cdcDisconnect').onclick=()=>api('usb/stop',{}).catch(e=>note(e.message,true));
  el('cdcSend').onclick=()=>api('usb/write',{session,hex:el('cdcHex').value.replace(/\s/g,'')}).catch(e=>note(e.message,true));
  async function poll(){
    try{
      const d=await api('usb/cdc');session=d.session;
      el('cdcState').textContent=JSON.stringify({état:d.state,source:d.status_source,transfert:d.transfer,erreur:d.error,motif:d.disconnect_reason||d.reason,dernière_commande:d.last_usb_control,endpoints:d.layout,octets_envoyés:d.sent_total,octets_reçus:d.received_total},null,2);
      el('cdcReceived').textContent=d.received_hex||'Aucun octet reçu';el('cdcSend').disabled=d.state!=='ready';
    }catch(e){el('cdcState').textContent=e.message;}
    if(!closed)setTimeout(poll,500);
  }
  poll();
})();
