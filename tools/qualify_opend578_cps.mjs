/* Real HTTP -> CDC -> independent ARM firmware qualification. No OEM inputs. */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
import {BenchHttpApi} from '../cps/src/device/bench-http.ts';
import {OpenD578ReadOnlyClient,assertOpenD578ReadOnly} from '../cps/src/device/opend578-readonly.ts';
const repo=fileURLToPath(new URL('../',import.meta.url));
const [pythonArg,binaryArg,outputArg]=process.argv.slice(2);
if(!pythonArg||!binaryArg||!outputArg)throw Error('Usage: node tools/qualify_opend578_cps.mjs PYTHON BINARY FRESH_RESULT_DIR');
const python=path.resolve(pythonArg),binary=path.resolve(binaryArg),output=path.resolve(outputArg);
fs.mkdirSync(output,{recursive:true});if(fs.existsSync(path.join(output,'stop.request')))throw Error('Choose a fresh result directory');
const bytes=fs.readFileSync(binary),signal=AbortSignal.timeout(180000);
const endpointFile=path.join(repo,'bench/work/web_endpoint.json');
const previousEndpoint=fs.existsSync(endpointFile)?fs.readFileSync(endpointFile):null;
const report={passed:false,scope:'HTTP/CDC/independent ARM bench; no physical radio',binarySHA256:crypto.createHash('sha256').update(bytes).digest('hex'),nativeCommands:[]};
let origin='',token='',server;
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function request(url,init={}){
 if(new URL(url).pathname==='/api/usb/write'){
  const packet=Buffer.from(JSON.parse(init.body).hex,'hex');assertOpenD578ReadOnly(packet);report.nativeCommands.push(packet.toString('ascii').trim().split(' ').at(-1));
 }
 return new Promise((resolve,reject)=>{
  const req=http.request(url,{method:init.method??'GET',headers:init.headers,agent:false,signal:init.signal??signal},res=>{
   const chunks=[];res.on('data',chunk=>chunks.push(chunk));res.on('end',()=>resolve(new Response(Buffer.concat(chunks),{status:res.statusCode})));
  });req.on('error',reject);req.end(init.body);
 });
}
async function api(route,data){
 const response=await request(origin+'/api/'+route,{method:data===undefined?'GET':'POST',headers:data===undefined?{}:{'Content-Type':Buffer.isBuffer(data)?'application/octet-stream':'application/json','X-Lab-Token':token,Origin:origin},body:data===undefined?undefined:Buffer.isBuffer(data)?data:JSON.stringify(data)});
 const result=await response.json();if(!response.ok)throw Error(result.error??`HTTP ${response.status}`);return result;
}
try{
 server=spawn(python,[path.join(repo,'bench/web_server.py'),'--port','0','--out-dir',output],{cwd:repo,windowsHide:true,env:{...process.env,PYTHONIOENCODING:'utf-8'}});
 origin=await new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>reject(Error('Server startup timeout')),15000);
  server.stdout.on('data',data=>{const match=String(data).match(/http:\/\/127\.0\.0\.1:\d+/);if(match){clearTimeout(timer);resolve(match[0]);}});
  server.stderr.on('data',data=>fs.appendFileSync(path.join(output,'server.log'),data));
  server.on('error',reject);server.on('exit',code=>{clearTimeout(timer);reject(Error(`Server exited: ${code}`));});
 });
 token=(await api('config')).token;
 await api('firmware',bytes);
 await api('start',{model:'hardware',boot:'application',engine:'native',firmware:'selected',nand:'blank',load_address:'auto',persist_nand:false,trace:false});
 while(true){
  signal.throwIfAborted();const status=await api('status');
  if(status.pixels>=20480){report.boot={steps:status.steps,pixels:status.pixels,engine:status.execution_engine};break;}
  if(!status.process_running||status.stop)throw Error(status.error??JSON.stringify(status.stop));
  await pause(100);
 }
 const transport=new BenchHttpApi({protocol:'opend578-ro',signal,fetcher:(route,init)=>request(origin+route,{...init,headers:{...init.headers,Origin:origin}})});await transport.initialize();
 const client=new OpenD578ReadOnlyClient((route,data)=>transport.request(route,data),{signal});
 const first=await client.readVfos();console.log('First HTTP VFO read passed');
 const second=await client.readVfos();
 if(first.engine!==second.engine||JSON.stringify(first.vfos)!==JSON.stringify(second.vfos))throw Error('Unexpected repeated-read result');
 if(first.vfos[0].rxHz!==145500000||first.vfos[1].rxHz!==435000000)throw Error('Unexpected alpha frequencies');
 if(first.capabilities.vfoWrite||first.capabilities.memories||first.capabilities.ctcss||first.capabilities.tx)throw Error('Unexpected capabilities');
 report.passed=true;report.firmware=first.firmware;report.capabilities=first.capabilities;report.vfos=first.vfos;report.sameEngineReadCount=2;
}catch(error){report.error=error.message;}
finally{
 fs.writeFileSync(path.join(output,'stop.request'),'stop');
 if(origin&&token){try{await api('shutdown',{});}catch{}}
 server?.kill();
 // Do not leave the bench's discovery record pointing at this closed test
 // server, and do not overwrite a newer endpoint created by somebody else.
 try{if(origin&&JSON.parse(fs.readFileSync(endpointFile,'utf8')).url===origin){if(previousEndpoint)fs.writeFileSync(endpointFile,previousEndpoint);else fs.unlinkSync(endpointFile);}}catch{}
 fs.writeFileSync(path.join(output,'qualification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));if(!report.passed)process.exitCode=1;
}
