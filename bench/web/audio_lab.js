(() => {
  const el=id=>document.getElementById(id);
  let capture=null,busy=false,playTimer=null;
  const message=s=>el('iqStatus').textContent=s;
  function buttons(){el('iqRecord').disabled=busy||!!capture;el('iqStop').disabled=!capture;el('iqAPRS').disabled=busy||!!capture;el('iqFile').disabled=busy||!!capture;}
  function config(){return {mic_gain_db:+el('iqMicGain').value,speaker_gain_db:+el('iqSpeakerGain').value,deviation_hz:+el('iqDeviation').value,channel_width_hz:+el('iqWidth').value,attenuation_db:+el('iqLoss').value,snr_db:+el('iqSNR').value,offset_hz:+el('iqOffset').value,rx_tune_hz:+el('iqTune').value,emphasis:el('iqEmphasis').checked};}
  function wav(chunks,rate){
    const count=chunks.reduce((n,c)=>n+c.length,0),buffer=new ArrayBuffer(44+count*2),v=new DataView(buffer);
    const str=(at,s)=>{for(let i=0;i<s.length;i++)v.setUint8(at+i,s.charCodeAt(i));};
    str(0,'RIFF');v.setUint32(4,36+count*2,true);str(8,'WAVE');str(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,rate,true);v.setUint32(28,rate*2,true);v.setUint16(32,2,true);v.setUint16(34,16,true);str(36,'data');v.setUint32(40,count*2,true);
    let at=44;for(const chunk of chunks)for(const sample of chunk){v.setInt16(at,Math.round(Math.max(-1,Math.min(1,sample))*32767),true);at+=2;}return new Uint8Array(buffer);
  }
  function base64(bytes){let s='';for(let at=0;at<bytes.length;at+=8192)s+=String.fromCharCode(...bytes.subarray(at,at+8192));return btoa(s);}
  async function run(mode,bytes){
    busy=true;buttons();clearTimeout(playTimer);el('iqPlayer').pause();message('Modulation, écriture et relecture des I/Q, puis réception…');
    try {
      const report=await api('audio/loop',{mode,config:config(),wav_base64:bytes?base64(bytes):undefined,source:el('iqCall').value,information:el('iqInfo').value});
      const base='/api/audio/'+report.session+'/';el('iqPlayer').src=base+'received.wav';el('iqPlayer').volume=.3;
      el('iqReport').textContent=JSON.stringify(report,null,2);el('iqDownloads').replaceChildren();
      for(const name of ['tx.sigmf-data','tx.sigmf-meta','rx.sigmf-data','rx.sigmf-meta','received.wav','report.json']){const a=document.createElement('a');a.href=base+name;a.download=name;a.textContent=name;el('iqDownloads').append(a,document.createElement('br'));}
      message(mode==='aprs'?'Réception : '+report.APRS_frames.length+' trame(s) avec CRC valide.':'Audio démodulé prêt.');
      const delay=Math.max(0,Math.min(10,+el('iqDelay').value||0));playTimer=setTimeout(()=>el('iqPlayer').play().catch(()=>message('Audio prêt : cliquer sur Lecture.')),delay*1000);
    }catch(e){message(e.message);}finally{busy=false;buttons();}
  }
  async function finish(){
    const c=capture;if(!c)return;capture=null;clearTimeout(c.timer);c.node.port.onmessage=null;c.stream.getTracks().forEach(t=>t.stop());c.source.disconnect();c.node.disconnect();c.mute.disconnect();await c.ctx.close();
    buttons();if(c.chunks.length)await run('fm',wav(c.chunks,c.rate));else message('Aucun échantillon reçu.');
  }
  el('iqRecord').onclick=async()=>{
    busy=true;buttons();let stream,ctx;
    try{
      stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:false,noiseSuppression:false,autoGainControl:false}});
      ctx=new AudioContext({sampleRate:48000});await ctx.audioWorklet.addModule('/audio_capture_worklet.js');await ctx.resume();
      const source=ctx.createMediaStreamSource(stream),node=new AudioWorkletNode(ctx,'iq-capture'),mute=ctx.createGain();mute.gain.value=0;source.connect(node);node.connect(mute);mute.connect(ctx.destination);
      const c={ctx,stream,source,node,mute,chunks:[],count:0,rate:ctx.sampleRate};capture=c;
      node.port.onmessage=e=>{if(capture!==c)return;const remaining=12*c.rate-c.count;if(remaining<=0){finish();return;}const chunk=e.data.slice(0,remaining);c.chunks.push(chunk);c.count+=chunk.length;if(c.count>=12*c.rate)finish();};
      c.timer=setTimeout(finish,12500);message('Enregistrement du micro… Terminer pour lancer la boucle.');
    }catch(e){stream?.getTracks().forEach(t=>t.stop());if(ctx)await ctx.close();message('Micro : '+e.message);}finally{busy=false;buttons();}
  };
  el('iqStop').onclick=finish;
  el('iqAPRS').onclick=()=>run('aprs');
  el('iqFile').onchange=async()=>{const file=el('iqFile').files[0];if(file){if(file.size>3*1024*1024){message('Fichier trop volumineux.');return;}await run('fm',new Uint8Array(await file.arrayBuffer()));}};
  window.addEventListener('pagehide',()=>{clearTimeout(playTimer);if(capture){capture.stream.getTracks().forEach(t=>t.stop());capture.ctx.close();}});
})();
