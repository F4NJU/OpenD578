import test from 'node:test';
import assert from 'node:assert/strict';
import { createCodeplug } from '../src/core/model.ts';
import type { Channel } from '../src/core/model.ts';
import { parseChannelsCsv, serializeChannelsCsv } from '../src/core/csv.ts';
import { EditorHistory, appendChannels, deleteChannels, moveItem } from '../src/core/editor.ts';

function channel(id = 'demo', name = 'Canal test'): Channel {
  return { id, name, mode: 'FM', rxHz: 145500001, txHz: 145000001, bandwidth: 'narrow', power: 'low', rxCtcssDeciHz: null, txCtcssDeciHz: 885, txInhibit: true };
}

test('CSV preserves exact frequencies, quotes, accents and formula-like names', () => {
  const channels = [channel('a', 'Relais, "été"'), channel('b', '=1+2'), channel('c', "'apostrophe"), channel('d', '-Canal')];
  const csv = serializeChannelsCsv(channels);
  assert(csv.includes("'="));
  assert.deepEqual(parseChannelsCsv(csv), channels);
  assert.deepEqual(parseChannelsCsv('\uFEFF' + serializeChannelsCsv([channel()]).replaceAll(',', ';')), [channel()]);
});

test('CSV refuses malformed fields, duplicate IDs and incomplete headers', () => {
  const csv = serializeChannelsCsv([channel()]);
  for (const source of [csv.replace('rx_mhz', 'frequency'), csv.replace('145.500001', '145.5000001'),
    csv.replace('true', 'yes'), csv.slice(0, -4) + '"', csv.replace('"low"', '"low"bad'),
    csv.replace('"low"', 'lo"w'), csv + csv.split('\r\n')[1] + '\r\n']) {
    assert.throws(() => parseChannelsCsv(source), source);
  }
});

test('CSV empty document is valid and spreadsheet CRLF does not create blank channels', () => {
  assert.deepEqual(parseChannelsCsv(serializeChannelsCsv([])), []);
  assert.equal(parseChannelsCsv(serializeChannelsCsv([channel()]) + '\r\n').length, 1);
});

test('CSV append is atomic on collision and retains zones and VFO', () => {
  const initial = { ...createCodeplug(), channels: [channel()], zones: [{ id: 'z', name: 'Zone', channelIds: ['demo'] }] };
  const before = structuredClone(initial);
  assert.throws(() => appendChannels(initial, [channel('new'), channel()]));
  assert.deepEqual(initial, before);
  const next = appendChannels(initial, [channel('new')]);
  assert.deepEqual(next.zones, initial.zones);
  assert.equal(next.channels.length, 2);
});

test('deleting shared channels removes all zone references and undo restores them', () => {
  const initial = { ...createCodeplug(), channels: [channel(), channel('other')], zones: [
    { id: 'a', name: 'A', channelIds: ['demo', 'other'] }, { id: 'b', name: 'B', channelIds: ['demo'] },
  ] };
  const editor = new EditorHistory(initial);
  editor.commit(deleteChannels(editor.value, ['demo']));
  assert.deepEqual(editor.value.zones.map(zone => zone.channelIds), [['other'], []]);
  editor.undo(); assert.deepEqual(editor.value, initial);
  editor.redo(); assert.equal(editor.value.channels.length, 1);
});

test('history isolates caller mutations, rejects invalid transactions and clears redo on edits', () => {
  const initial = createCodeplug();
  const editor = new EditorHistory(initial);
  initial.name = 'Changed outside';
  assert.equal(editor.value.name, 'Nouveau codeplug');
  const snapshot = editor.value; snapshot.name = 'Outside again';
  assert.equal(editor.value.name, 'Nouveau codeplug');
  assert.throws(() => editor.commit({ ...editor.value, name: '' }));
  assert.equal(editor.canUndo, false);
  editor.commit({ ...editor.value, name: 'First' });
  editor.commit(editor.value); editor.undo();
  assert.equal(editor.value.name, 'Nouveau codeplug');
  assert(editor.canRedo);
  editor.commit({ ...editor.value, name: 'Second' });
  assert.equal(editor.canRedo, false);
});

test('reordering is immutable and handles boundary moves', () => {
  const items = ['a', 'b', 'c'];
  assert.deepEqual(moveItem(items, 1, -1), ['b', 'a', 'c']);
  assert.deepEqual(moveItem(items, 0, -1), items);
  assert.deepEqual(moveItem(items, 2, 1), items);
  assert.deepEqual(items, ['a', 'b', 'c']);
});
