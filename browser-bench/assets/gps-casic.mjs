/* CASIC V3.6 §§1.6.3-1.6.5; only the OEM-observed PCAS02/03/04 subset.
 * Input commands configure an external NMEA source. No ACK or fix is invented.
 * Manufacturer protocol: https://www.espruino.com/files/CASIC_en.pdf */
export class CAsicControl {
 constructor(){this.buffer='';this.intervalMs=null;this.rates=null;this.systemMask=null;this.accepted=0;this.rejected=0;this.unsupported=0;this.disconnectedBytes=0;this.history=[];}
 input(byte,{connected=true,sourceByteSteps=null,receiverBaud=9600}={}){
  if(!connected){this.buffer='';this.disconnectedBytes++;return false;}
  if(sourceByteSteps!==null&&Math.abs(sourceByteSteps-120000000*10/receiverBaud)/sourceByteSteps>0.03){this.buffer='';this.rejected++;return false;}
  if(byte===36){this.buffer='$';return false;}if(!this.buffer)return false;
  if(byte===10){const text=this.buffer;this.buffer='';return this.command(text);}
  if(byte===13)return false;
  if(byte<32||byte>126||this.buffer.length>=160){this.buffer='';this.rejected++;return false;}
  this.buffer+=String.fromCharCode(byte);return false;
 }
 command(text){
  const match=/^\$(PCAS\d{2}(?:,[0-9,]*)?)\*([A-Fa-f0-9]{2})$/.exec(text);
  if(!match){this.rejected++;return false;}let sum=0;for(const c of match[1])sum^=c.charCodeAt(0);
  if(sum!==parseInt(match[2],16)){this.rejected++;return false;}
  const [name,...fields]=match[1].split(',');let accepted=false;
  if(name==='PCAS02'&&fields.length===1&&['100','200','250','500','1000'].includes(fields[0])){this.intervalMs=Number(fields[0]);accepted=true;}
  if(name==='PCAS03'&&fields.length===8&&fields.every(f=>/^\d?$/.test(f))){
   const old=this.rates??{GGA:1,GLL:0,GSA:0,GSV:1,RMC:1,VTG:0,ZDA:0,TXT:0};
   this.rates=Object.fromEntries(['GGA','GLL','GSA','GSV','RMC','VTG','ZDA','TXT'].map((k,i)=>[k,fields[i]===''?old[k]:Number(fields[i])]));accepted=true;
  }
  if(name==='PCAS04'&&fields.length===1&&/^[1-7]$/.test(fields[0])){this.systemMask=Number(fields[0]);accepted=true;}
  if(!accepted){if(['PCAS02','PCAS03','PCAS04'].includes(name))this.rejected++;else this.unsupported++;return false;}
  this.accepted++;this.history.push({name,raw:text});if(this.history.length>16)this.history.shift();return true;
 }
 filter(text,epoch){
  if(!this.rates)return text;
  const unsupported=['GLL','GSA','ZDA'].filter(k=>this.rates[k]>0);if(unsupported.length)throw Error('CASIC phrases demandées non portées : '+unsupported.join(', '));
  return text.split('\r\n').filter(s=>{if(!s)return false;const kind=s.slice(3,6),n=this.rates[kind]??0;return n>0&&epoch%n===0;}).join('\r\n').replace(/(.+)$/s,'$1\r\n');
 }
 talker(fallback){return this.systemMask===1?'GP':this.systemMask===2?'BD':this.systemMask===4?'GL':this.systemMask===null?fallback:'GN';}
 status(){return {profile:'CASIC V3.6 PCAS02/03/04 subset',intervalMs:this.intervalMs,rates:this.rates,systemMask:this.systemMask,accepted:this.accepted,rejected:this.rejected,unsupported:this.unsupported,disconnectedBytes:this.disconnectedBytes,pendingBytes:this.buffer.length,history:this.history.slice(),generatedACKs:0,physicalReceiverFirmwareExecuted:false};}
}
