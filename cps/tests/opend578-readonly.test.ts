import test from 'node:test';
import assert from 'node:assert/strict';
import { OpenD578ReadOnlyClient, assertOpenD578ReadOnly } from '../src/device/opend578-readonly.ts';
import { BenchHttpApi } from '../src/device/bench-http.ts';
import type { BenchApi } from '../src/device/oem-readonly.ts';

// Host fixtures only. Firmware qualification executes the real ARM binary separately.
function nativeWire(fault = '', fragmented = false) {
  let sent = 0, total = 0, pending = new Uint8Array(); const requests: string[] = [];
  const state = () => ({state:'ready',session:'s',engine_instance:'e',sent_total:sent,received_total:total,queued_bytes:0});
  const api: BenchApi = async (path,data) => {
    if(path.endsWith('view=summary')) return state();
    if(path==='usb/write') {
      const bytes=Uint8Array.from(Buffer.from(String(data!.hex),'hex'));assertOpenD578ReadOnly(bytes);sent+=bytes.length;
      const text=new TextDecoder().decode(bytes);requests.push(text);const [,id,command]=text.trim().split(' ');
      const reply:Record<string,unknown>={protocol:'opend578-cps',version:1,id:Number(id)};
      if(command==='HELLO')Object.assign(reply,{firmware:'rx-fm-alpha-cps-ro.1',capabilities:{vfoRead:true,vfoWrite:false,memories:false,ctcss:false,dcs:false,tx:false,persistent:false}});
      else Object.assign(reply,{selected:'A',vfos:[{id:'A',rxHz:145500000,bandwidth:'wide',txInhibit:true},{id:'B',rxHz:435000000,bandwidth:'narrow',txInhibit:true}]});
      if(fault==='id')reply.id=999;
      if(fault==='protocol')reply.protocol='oem';
      if(fault==='capabilities'&&command==='HELLO')(reply.capabilities as Record<string,unknown>).ctcss='unknown';
      if(fault==='vfo'&&command==='VFOS')(reply.vfos as Record<string,unknown>[])[0].txInhibit=false;
      pending=new TextEncoder().encode(JSON.stringify(reply)+'\n'+(fault==='extra'?'{}\n':''));return {queued:true};
    }
    const part=fragmented?pending.slice(0,25):pending;pending=pending.slice(part.length);const base=total;total+=part.length;
    return {...state(),engine_instance:fault==='engine'?'different':'e',received_base:base,received_hex:Buffer.from(part).toString('hex')};
  };
  return {api,requests};
}

test('OpenD578 live VFO read is versioned, fragmented and repeatable without PROGRAM or END', async () => {
  const wire=nativeWire('',true),client=new OpenD578ReadOnlyClient(wire.api);
  const first=await client.readVfos(),second=await client.readVfos();
  assert.equal(first.vfos[0].rxHz,145500000);assert.equal(first.vfos[1].bandwidth,'narrow');assert.equal(first.capabilities.ctcss,false);
  assert.equal(second.engine,first.engine);assert.equal(wire.requests.length,4);
  assert(wire.requests.every(value=>/^OD578\/1 \d+ (HELLO|VFOS)\n$/.test(value)));
});

test('unexpected identity, versioned response, capabilities, TX state and extra/foreign traffic are refused', async () => {
  for(const fault of ['id','protocol','capabilities','vfo','extra','engine']) {
    const wire=nativeWire(fault);await assert.rejects(new OpenD578ReadOnlyClient(wire.api).readVfos());
    assert(wire.requests.length<=2);
  }
  const wire=nativeWire(),abort=new AbortController();abort.abort();
  await assert.rejects(new OpenD578ReadOnlyClient(wire.api,{signal:abort.signal}).readVfos());assert.equal(wire.requests.length,0);
});

test('native HTTP transport permits only native read requests and keeps the OEM guard as default', async () => {
  for(const text of ['PROGRAM','END','W','OD578/1 1 WRITE\n','OD578/1 65536 HELLO\n','OD578/1 1 VFOS\nOD578/1 2 VFOS\n'])assert.throws(()=>assertOpenD578ReadOnly(new TextEncoder().encode(text)));
  let calls=0;
  const fetcher=(async()=>{calls++;return Response.json({token:'t',capabilities:{usb_cdc:true}});}) as typeof fetch;
  const native=new BenchHttpApi({protocol:'opend578-ro',fetcher});await native.initialize();
  const hex=(text:string)=>Buffer.from(text).toString('hex');
  await native.request('usb/write',{session:'s',hex:hex('OD578/1 1 HELLO\n')});
  await assert.rejects(native.request('usb/write',{session:'s',hex:hex('PROGRAM')}));
  const oem=new BenchHttpApi({fetcher});await oem.initialize();
  await assert.rejects(oem.request('usb/write',{session:'s',hex:hex('OD578/1 1 VFOS\n')}));
  assert.equal(calls,3);
});
