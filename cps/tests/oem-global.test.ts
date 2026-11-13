import test from 'node:test';
import assert from 'node:assert/strict';
import { OEM_BITMAP, oemActiveSlots, oemChannelAddress, oemReadableAddress, decodeOemTone } from '../src/device/oem-profile.ts';
import { OemReadOnlyClient, assertOemReadOnly, decodeOemPage } from '../src/device/oem-readonly.ts';
import type { BenchApi, OemSnapshot } from '../src/device/oem-readonly.ts';
import { appendOemSlots, mergeOemSnapshots, oemImportReason } from '../src/core/oem-import.ts';
import { createCodeplug } from '../src/core/model.ts';

test('4000 channel banks and bitmap are bounded; gaps, VFO and calibration remain forbidden', () => {
  assert.equal(oemChannelAddress(129), 0x840000); assert.equal(oemChannelAddress(4000), 0xfc07c0);
  for (let slot = 1; slot <= 4000; slot++) for (let i = 0; i < 64; i += 16) assert.ok(oemReadableAddress(oemChannelAddress(slot) + i));
  for (const address of [0x802000, 0x83fff0, 0xfc0800, 0x2f00000, OEM_BITMAP - 16, OEM_BITMAP + 512, OEM_BITMAP + 1]) assert.equal(oemReadableAddress(address), false);
  assert.throws(() => oemChannelAddress(4001));
  assert.equal(oemActiveSlots(new Uint8Array(512).fill(255)).length, 4000);
  const bitmap = new Uint8Array(512); bitmap[0] = 1; bitmap[16] = 1; bitmap[499] = 128; bitmap[511] = 255;
  assert.deepEqual(oemActiveSlots(bitmap), [1,129,4000]);
});

test('RX/TX tones preserve none, independent CTCSS indices, custom tones and DCS inversion', () => {
  const record = new Uint8Array(64); record[10] = 19; record[11] = 9;
  assert.deepEqual(decodeOemTone(record, 'rx'), {kind:'none'});
  record[9] = 5;
  assert.deepEqual(decodeOemTone(record, 'rx'), {kind:'ctcss',deciHz:885});
  assert.deepEqual(decodeOemTone(record, 'tx'), {kind:'ctcss',deciHz:1230});
  record[10] = 0; assert.deepEqual(decodeOemTone(record,'tx'),{kind:'ctcss',deciHz:625});
  record[11] = 51; record[16] = 0x79; record[17] = 3;
  assert.deepEqual(decodeOemTone(record,'rx'),{kind:'ctcss',deciHz:889});
  record[9] = 2; record[14] = 19; record[15] = 2;
  assert.deepEqual(decodeOemTone(record,'rx'),{kind:'dcs',code:'023',inverted:true});
  record[9] = 3; assert.equal(decodeOemTone(record,'rx').kind,'unknown');
  record[9] = 1; record[11] = 255; assert.equal(decodeOemTone(record,'rx').kind,'unknown');
});

function globalWire(corrupt = false) {
  const bitmap = new Uint8Array(512); bitmap[0] = 1; bitmap[16] = 1; bitmap[499] = 128;
  let sent = 0, total = 0, pending = new Uint8Array(); const requests: Uint8Array[] = [];
  const state = () => ({ state:'ready',engine_instance:'global-engine',session:'s',sent_total:sent,queued_bytes:0,received_total:total,received_base:total,received_hex:'' });
  const api: BenchApi = async (path, data) => {
    if (path.endsWith('view=summary')) return state();
    if (path === 'usb/write') {
      const request = Uint8Array.from(Buffer.from(String(data!.hex),'hex')); assertOemReadOnly(request); requests.push(request); sent += request.length;
      if (request[0] === 80) pending = Uint8Array.from([81,88,6]);
      else if (request[0] === 2) { pending = new Uint8Array(16); pending.set([73,68,53,55,56,85,86,0]); pending[15] = 6; }
      else if (request[0] === 82) {
        const address = request[1]*0x1000000+(request[2]<<16)+(request[3]<<8)+request[4];
        const record = new Uint8Array(64); record.set([0x14,0x55,0,0]); record[9]=5; record[10]=19; record[11]=9; record.set(new TextEncoder().encode('SYNTH'),35);
        const payload = address >= OEM_BITMAP && address < OEM_BITMAP+512 ? bitmap.slice(address-OEM_BITMAP,address-OEM_BITMAP+16) : record.slice(address%64,address%64+16);
        pending = new Uint8Array(24); pending.set(request); pending[0]=87; pending.set(payload,6); pending[22]=pending.slice(1,22).reduce((a,b)=>a+b,0)&255; pending[23]=6;
        if(corrupt && address===OEM_BITMAP+16) pending[22]^=1;
      } else pending=Uint8Array.of(6);
      return {queued:true};
    }
    const reply=pending; pending=new Uint8Array(); const base=total; total+=reply.length;
    return {...state(),received_base:base,received_hex:Buffer.from(reply).toString('hex')};
  };
  return {api,requests};
}

test('global read follows active bitmap across banks, returns one complete import and a single END', async () => {
  const wire=globalWire(); const snapshot=await new OemReadOnlyClient(wire.api).readAll();
  assert.equal(snapshot.scope,'active-channels'); assert.deepEqual(snapshot.slots.map(s=>s.slot),[1,129,4000]);
  assert.equal(snapshot.endAcknowledged,true); assert.equal(wire.requests.length,47);
  let id=0; const next=appendOemSlots(createCodeplug(),snapshot,[129,4000],{bandwidth:'narrow',power:'low'},()=>`id${++id}`);
  assert.equal(next.channels.length,2); assert.equal(next.channels[0].rxCtcssDeciHz,885); assert.equal(next.channels[0].txCtcssDeciHz,1230);
  assert.equal(next.channels[0].txInhibit,true);
  const dcs={...snapshot.slots[0],rxTone:{kind:'dcs' as const,code:'023',inverted:false}};
  assert.match(oemImportReason(dcs)!,/DCS/);
});

test('bad bitmap reply and cancellation stop without END or a partial global result', async () => {
  const bad=globalWire(true); await assert.rejects(new OemReadOnlyClient(bad.api).readAll()); assert.equal(bad.requests.at(-1)![0],82);
  const wire=globalWire(), abort=new AbortController();
  await assert.rejects(new OemReadOnlyClient(wire.api,{signal:abort.signal,progress:()=>abort.abort()}).readAll());
  assert.equal(wire.requests.length,3); assert.equal(wire.requests.at(-1)![0],82);
});

test('page accumulation deduplicates slots, replaces rereads and never merges different engines', () => {
  const bytes=new Uint8Array(2048); const first:OemSnapshot={engine:'one',model:'D578UV',page:0,readAt:'test',endAcknowledged:false,slots:decodeOemPage(bytes,0)};
  const second={...first,page:1,slots:decodeOemPage(bytes,1)};
  const merged=mergeOemSnapshots(first,second); assert.equal(merged.slots.length,64);
  assert.equal(mergeOemSnapshots(merged,first).slots.length,64);
  assert.equal(mergeOemSnapshots(merged,{...second,engine:'two'}).slots.length,32);
  assert.throws(()=>appendOemSlots(createCodeplug(),merged,[1],{bandwidth:'narrow',power:'low'}));
});
