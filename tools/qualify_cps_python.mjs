/* Execute the OEM Python bench and the real CPS client over its HTTP/CDC API.
 * No firmware responses, NAND bytes or identities are synthesized here. */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {BenchHttpApi} from '../cps/src/device/bench-http.ts';
import {OemReadOnlyClient,assertOemReadOnly} from '../cps/src/device/oem-readonly.ts';

const repo=fileURLToPath(new URL('../',import.meta.url));
const [pythonArg,sourceArg,outputArg]=process.argv.slice(2);
if(!pythonArg||!sourceArg||!outputArg)throw Error('Usage: node tools/qualify_cps_python.mjs PYTHON CAPTURE_DIR RESULT_DIR');
const python=path.resolve(pythonArg),source=path.resolve(sourceArg),output=path.resolve(outputArg);
const engine=process.env.OPEND578_BENCH_ENGINE??'python';
if(!['python','native','interactive'].includes(engine))throw Error('Invalid bench engine');
fs.mkdirSync(output,{recursive:true});
if(fs.existsSync(path.join(output,'stop.request')))throw Error('Choose a fresh result directory.');
const report={schema:'opend578.real-oem-cps-readonly.v1',engine,passed:false,firmwareExecuted:false,httpExercised:false,physicalRadio:false,usbFramesSubmitted:0,writeCommandsSubmitted:0};
const bootTimeout=Number(process.env.OPEND578_BOOT_TIMEOUT_MS??300000);
if(!Number.isInteger(bootTimeout)||bootTimeout<1000||bootTimeout>600000)throw Error('Invalid boot timeout');
const deadline=AbortSignal.timeout(bootTimeout+90000);
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
let origin='',token='',server;
// Plain HTTP transport to the locally spawned server, without an environment proxy.
function request(url,init={}) {
  if(new URL(url).pathname==='/api/usb/write'){
    const frame=Buffer.from(JSON.parse(init.body).hex,'hex');
    assertOemReadOnly(frame);
    report.usbFramesSubmitted++;
    if(frame[0]===0x57)report.writeCommandsSubmitted++;
  }
  return new Promise((resolve,reject)=>{
    const req=http.request(url,{method:init.method??'GET',headers:init.headers,agent:false,signal:init.signal??AbortSignal.timeout(5000)},res=>{
      const chunks=[];res.on('data',chunk=>chunks.push(chunk));res.on('end',()=>resolve(new Response(Buffer.concat(chunks),{status:res.statusCode})));
    });
    req.on('error',reject);req.end(init.body);
  });
}
async function api(route,data){
  const response=await request(origin+'/api/'+route,{method:data===undefined?'GET':'POST',headers:data===undefined?{}:{'Content-Type':'application/json','X-Lab-Token':token,Origin:origin},body:data===undefined?undefined:JSON.stringify(data),signal:AbortSignal.any([deadline,AbortSignal.timeout(10000)])});
  const body=await response.json();if(!response.ok)throw Error(body.error??`HTTP ${response.status}`);return body;
}
try {
  server=spawn(python,[path.join(repo,'bench/web_server.py'),'--port','0','--source-dir',source,'--cache-dir',path.join(repo,'bench/work/inputs'),'--out-dir',output],{cwd:repo,windowsHide:true,env:{...process.env,PYTHONIOENCODING:'utf-8'}});
  origin=await new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>reject(Error('Server startup timeout')),20000);
    server.stdout.on('data',data=>{const match=String(data).match(/http:\/\/127\.0\.0\.1:\d+/);if(match){clearTimeout(timer);resolve(match[0]);}});
    server.on('error',reject);server.on('exit',code=>{clearTimeout(timer);reject(Error(`Server exited: ${code}`));});
    server.stderr.on('data',data=>fs.appendFileSync(path.join(output,'server.log'),data));
  });
  const config=await api('config');token=config.token;report.httpExercised=true;
  await api('start',{model:'oem',boot:'application',engine,source,persist_nand:false,trace:false,voltage:13.8});
  const bootDeadline=Date.now()+bootTimeout;let nextProgress=0;
  while(true){
    deadline.throwIfAborted();const state=await api('status');
    report.firmwareExecuted ||= state.steps>0;
    report.lastBoot={steps:state.steps,pixels:state.pixels,modelSeconds:state.model_seconds,applicationRunning:state.application_running};
    if(state.application_running){report.boot=report.lastBoot;break;}
    if(!state.process_running||state.stop||Date.now()>bootDeadline)throw Error(state.error??state.stop?.kind??'OEM startup not ready within bound');
    if(Date.now()>nextProgress){console.log(JSON.stringify({phase:'boot',steps:state.steps,pixels:state.pixels,modelSeconds:state.model_seconds}));nextProgress=Date.now()+5000;}
    await delay(250);
  }
  const transport=new BenchHttpApi({signal:deadline,fetcher:(route,init)=>request(origin+route,{...init,headers:{...init.headers,Origin:origin}})});
  await transport.initialize();
  const snapshot=await new OemReadOnlyClient((route,data)=>transport.request(route,data),{signal:deadline,progress:(done,total)=>{if(done%512===0)console.log(JSON.stringify({phase:'read',done,total}));}}).readPage(0);
  report.passed=true;report.model=snapshot.model;report.slotCount=snapshot.slots.length;report.endAcknowledged=snapshot.endAcknowledged;
  report.slotSnapshotSha256=crypto.createHash('sha256').update(JSON.stringify(snapshot.slots)).digest('hex');
}catch(error){report.error=error.message;}
finally{
  fs.writeFileSync(path.join(output,'stop.request'),'stop');
  if(origin&&token){try{await api('shutdown',{});}catch{}}
  server?.kill();
  fs.writeFileSync(path.join(output,'qualification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report,null,2));if(!report.passed)process.exitCode=1;
}
