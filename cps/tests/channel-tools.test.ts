import test from 'node:test';
import assert from 'node:assert/strict';
import { createCodeplug } from '../src/core/model.ts';
import type { Codeplug } from '../src/core/model.ts';
import { createChannelSeries, reviewCodeplug, txFromOffset } from '../src/core/channel-tools.ts';
import { EditorHistory } from '../src/core/editor.ts';
import { readFrequencies, readPower, powerField } from '../src/ui/channel-fields.ts';

function template(): Codeplug {
  return { ...createCodeplug(), channels: [{ id: 'source', name: 'Relais', mode: 'FM', rxHz: 145600001, txHz: 145000001,
    bandwidth: 'narrow', power: 'association', rxCtcssDeciHz: 1230, txCtcssDeciHz: 885, txInhibit: true }],
    zones: [{ id: 'zone', name: 'Zone', channelIds: ['source'] }] };
}
function fields(values: Record<string, string>): FormData {
  const data = new FormData(); for (const [key, value] of Object.entries(values)) data.set(key, value); return data;
}

test('relay offset preserves individual Hz and rejects invalid TX results', () => {
  assert.equal(txFromOffset(145600001, 'minus', 600000), 145000001);
  assert.equal(txFromOffset(430000001, 'plus', 7600000), 437600001);
  assert.equal(txFromOffset(145500001, 'simplex', 600000), 145500001);
  for (const action of [() => txFromOffset(1, 'minus', 1), () => txFromOffset(1.5, 'plus', 1),
    () => txFromOffset(Number.MAX_SAFE_INTEGER, 'plus', 1), () => txFromOffset(10, 'minus', -1)]) assert.throws(action);
});

test('frequency form calculates from shift inputs and respects independent TX', () => {
  assert.deepEqual(readFrequencies(fields({ rx: '145,600001', tx: '1', 'shift-mode': 'minus', 'shift-value': '0,600000' })), { rxHz: 145600001, txHz: 145000001 });
  assert.equal(readFrequencies(fields({ rx: '145.5', tx: '433.5', 'shift-mode': 'direct' })).txHz, 433500000);
  assert.equal(readFrequencies(fields({ rx: '145.5', 'shift-mode': 'simplex' })).txHz, 145500000);
  assert.equal(readFrequencies(fields({ rx: '145.5', 'shift-mode': 'plus', 'shift-value': '0' })).txHz, 145500000);
  assert.throws(() => readFrequencies(fields({ rx: '145.5', 'shift-mode': 'minus', 'shift-value': '0.0000001' })));
});

test('series retains settings and shift, generates fresh IDs, appends to zone and undoes atomically', () => {
  const source = template(), before = structuredClone(source); let sequence = 0;
  const history = new EditorHistory(source);
  history.commit(createChannelSeries(source, 'source', 3, 12500, () => `copy-${++sequence}`, 'zone'));
  const next = history.value;
  assert.equal(next.channels.length, 4); assert.deepEqual(next.zones[0].channelIds, ['source', 'copy-1', 'copy-2', 'copy-3']);
  assert.equal(next.channels[1].rxHz, 145612501); assert.equal(next.channels[3].rxHz, 145637501);
  assert.equal(next.channels[3].txHz - next.channels[3].rxHz, -600000);
  assert.equal(next.channels[1].power, 'association'); assert.equal(next.channels[1].txInhibit, true);
  assert.equal(next.channels[1].txCtcssDeciHz, 885); assert.equal(next.channels[1].rxCtcssDeciHz, 1230);
  assert.deepEqual(source, before);
  history.undo(); assert.deepEqual(history.value, before);
});

test('series refuses invalid counts, zero step, collisions and frequency underflow without partial edits', () => {
  const source = template(), before = structuredClone(source); let id = 0;
  for (const [count, step] of [[0, 12500], [257, 12500], [1.5, 12500], [2, 0], [2, -145000001]]) {
    assert.throws(() => createChannelSeries(source, 'source', count, step, () => `x-${++id}`));
  }
  assert.throws(() => createChannelSeries(source, 'source', 2, 12500, () => 'source'));
  assert.throws(() => createChannelSeries(source, 'absent', 2, 12500, () => `x-${++id}`));
  assert.throws(() => createChannelSeries(source, 'source', 2, 12500, () => `x-${++id}`, 'missing'));
  assert.deepEqual(source, before);
  assert.equal(createChannelSeries(source, 'source', 1, -12500, () => 'lower').channels[1].rxHz, 145587501);
});

test('power choices preserve custom identifiers and distinguish keep from empty custom input', () => {
  assert.equal(readPower(fields({ 'power-choice': 'value:high' })), 'high');
  assert.equal(readPower(fields({ 'power-choice': 'value:association' })), 'association');
  assert.equal(readPower(fields({ 'power-choice': 'custom', 'power-custom': '  terrain  ' })), 'terrain');
  assert.equal(readPower(fields({ 'power-choice': 'keep' })), '');
  assert.throws(() => readPower(fields({ 'power-choice': 'custom', 'power-custom': '  ' })));
  assert(powerField('association').includes('value:association'));
});

test('document review separates invalid data from nonblocking duplicate and empty-list warnings', () => {
  assert(reviewCodeplug(null).every(finding => finding.severity === 'error'));
  const value = template();
  assert.deepEqual(reviewCodeplug(value), []);
  value.channels.push({ ...value.channels[0], id: 'other', name: 'relais' });
  value.zones.push({ id: 'empty', name: 'Vide', channelIds: [] });
  const report = reviewCodeplug(value);
  assert(report.every(finding => finding.severity === 'warning'));
  for (const code of ['duplicate_name', 'duplicate_frequencies', 'empty_list']) assert(report.some(finding => finding.code === code));
  assert(reviewCodeplug(createCodeplug()).some(finding => finding.code === 'empty_document'));
});
