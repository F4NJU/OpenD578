import test from 'node:test';
import assert from 'node:assert/strict';
import { appendOemSlots, oemImportReason } from '../src/core/oem-import.ts';
import { createCodeplug } from '../src/core/model.ts';
import { EditorHistory } from '../src/core/editor.ts';
import { parseCodeplug, serializeCodeplug } from '../src/core/json.ts';
import { decodeOemPage } from '../src/device/oem-readonly.ts';
import type { OemSnapshot } from '../src/device/oem-readonly.ts';

function snapshot(): OemSnapshot {
  const bytes = new Uint8Array(2048).fill(255);
  bytes.fill(0, 0, 64); bytes.set([0x14, 0x55, 0, 0, 0, 0x06, 0, 0, 0x40]);
  bytes.set(new TextEncoder().encode('TEST'), 35);
  return { engine: 'test', model: 'D578UV', page: 0, readAt: new Date().toISOString(), slots: decodeOemPage(bytes, 0), endAcknowledged: true };
}

test('OEM preparation adds selected FM slots with explicit settings, TX inhibited and atomic undo', () => {
  const source = snapshot(), original = structuredClone(source), value = createCodeplug();
  value.zones.push({ id: 'z1', name: 'Existing', channelIds: [] });
  value.scanLists.push({ id: 's1', name: 'Existing scan', channelIds: [], priorityChannelId: null });
  const next = appendOemSlots(value, source, [1], { bandwidth: 'wide', power: 'customPower' }, () => 'fresh1');
  assert.deepEqual(next.channels[0], { id: 'fresh1', name: 'TEST', mode: 'FM', rxHz: 145500000, txHz: 146100000,
    bandwidth: 'wide', power: 'customPower', rxCtcssDeciHz: null, txCtcssDeciHz: null, txInhibit: true });
  assert.deepEqual(next.zones, value.zones); assert.deepEqual(next.scanLists, value.scanLists); assert.equal(next.vfo, value.vfo);
  assert.equal(value.channels.length, 0); assert.deepEqual(source, original);
  const history = new EditorHistory(value); history.commit(next); history.undo(); assert.deepEqual(history.value, value);
  history.redo(); assert.deepEqual(parseCodeplug(serializeCodeplug(history.value)), next);
});

test('unknown values and digital or mixed modes cannot be silently converted to FM', () => {
  const source = snapshot();
  for (const mode of ['DMR', 'FM + DMR RX', 'DMR + FM RX']) {
    source.slots[0].mode = mode;
    assert.throws(() => appendOemSlots(createCodeplug(), source, [1], { bandwidth: 'narrow', power: 'low' }));
  }
  source.slots[0].mode = 'FM'; source.slots[0].rxHz = null;
  assert.ok(oemImportReason(source.slots[0])); source.slots[0].rxHz = 145500000; source.slots[0].name = '   ';
  assert.ok(oemImportReason(source.slots[0]));
});

test('invalid or duplicate selection, incomplete session and ID collisions leave document untouched', () => {
  const source = snapshot(), value = createCodeplug(), before = structuredClone(value), settings = { bandwidth: 'narrow' as const, power: 'low' };
  for (const selected of [[], [1, 1], [33], [1, 2]]) assert.throws(() => appendOemSlots(value, source, selected, settings));
  assert.throws(() => appendOemSlots(value, { ...source, endAcknowledged: false } as unknown as OemSnapshot, [1], settings));
  assert.throws(() => appendOemSlots(value, source, [1], { ...settings, bandwidth: '' as 'narrow' }));
  const once = appendOemSlots(value, source, [1], settings, () => 'id1');
  assert.throws(() => appendOemSlots(once, source, [1], settings, () => 'id1'));
  assert.deepEqual(value, before);
});
