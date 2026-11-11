import test from 'node:test';
import assert from 'node:assert/strict';
import { createCodeplug } from '../src/core/model.ts';
import type { Codeplug, DeviceCapabilities } from '../src/core/model.ts';
import { parseCodeplug, serializeCodeplug } from '../src/core/json.ts';
import { validateCodeplug } from '../src/core/validation.ts';
import { deleteChannels, EditorHistory } from '../src/core/editor.ts';
import { validateForDevice } from '../src/core/capabilities.ts';

function scanFixture(): Codeplug {
  const channels = ['a', 'b'].map(id => ({ id, name: id, mode: 'FM' as const,
    rxHz: 145500000, txHz: 145500000, bandwidth: 'narrow' as const, power: 'low',
    rxCtcssDeciHz: null, txCtcssDeciHz: null, txInhibit: true }));
  return { ...createCodeplug(), channels, scanLists: [
    { id: 'scan', name: 'Terrain', channelIds: ['b', 'a'], priorityChannelId: 'a' },
  ] };
}

test('v1 migration requires explicit opt-in and preserves all legacy data', () => {
  const current = scanFixture();
  const { scanLists: _scanLists, ...fields } = current;
  const legacy = { ...fields, schemaVersion: 1 };
  const source = JSON.stringify(legacy);
  assert.throws(() => parseCodeplug(source));
  const upgraded = parseCodeplug(source, { upgradeV1: true });
  assert.deepEqual(upgraded, { ...legacy, schemaVersion: 2, scanLists: [] });
  assert.equal(JSON.stringify(legacy), source);
  assert.deepEqual(parseCodeplug(serializeCodeplug(upgraded)), upgraded);
  assert.throws(() => parseCodeplug(JSON.stringify({ ...legacy, calibration: {} }), { upgradeV1: true }));
  assert.throws(() => parseCodeplug(JSON.stringify({ ...legacy, scanLists: [] }), { upgradeV1: true }));
});

test('scan lists keep membership order and priority through JSON and channel reordering', () => {
  const value = scanFixture();
  const updated = { ...value, channels: [...value.channels].reverse() };
  assert.deepEqual(parseCodeplug(serializeCodeplug(updated)).scanLists, value.scanLists);
});

test('invalid lists cannot leave dangling members or a priority outside membership', () => {
  for (const mutate of [
    (value: Codeplug) => { value.scanLists[0].channelIds = ['missing']; },
    (value: Codeplug) => { value.scanLists[0].channelIds = ['a', 'a']; },
    (value: Codeplug) => { value.scanLists[0].priorityChannelId = 'missing'; },
    (value: Codeplug) => { value.scanLists[0].channelIds = ['b']; },
    (value: Codeplug) => { value.scanLists.push(structuredClone(value.scanLists[0])); },
    (value: Codeplug) => { value.scanLists[0].name = ''; },
    (value: Codeplug) => { Object.assign(value.scanLists[0], { unknown: true }); },
    (value: Codeplug) => { value.scanLists.length += 1; },
  ]) {
    const value = scanFixture(); mutate(value);
    assert(validateCodeplug(value).some(issue => issue.path.startsWith('$.scanLists')));
    assert.throws(() => serializeCodeplug(value));
  }
});

test('deleting a priority channel cleans all references and undo restores the exact list', () => {
  const initial = scanFixture();
  initial.zones = [{ id: 'z', name: 'Zone', channelIds: ['a', 'b'] }];
  const history = new EditorHistory(initial);
  history.commit(deleteChannels(history.value, ['a']));
  assert.deepEqual(history.value.scanLists[0], { id: 'scan', name: 'Terrain', channelIds: ['b'], priorityChannelId: null });
  assert.deepEqual(history.value.zones[0].channelIds, ['b']);
  history.undo(); assert.deepEqual(history.value, initial);
  history.redo(); assert.equal(history.value.scanLists[0].priorityChannelId, null);
});

test('a target without declared scan capabilities refuses scan data', () => {
  const target: DeviceCapabilities = { maxChannels: 2, maxZones: 0, maxChannelsPerZone: 0, maxNameBytes: 32,
    rxBands: [{ minHz: 144000000, maxHz: 146000000 }], txBands: [],
    bandwidths: ['narrow'], powerLevels: ['low'], ctcssDeciHz: [], supportsVfo: false };
  assert(validateForDevice(scanFixture(), target).some(issue => issue.path === '$.scanLists'));
  const supported = { ...target, maxScanLists: 1, maxChannelsPerScanList: 2, supportsScanPriority: true };
  assert.deepEqual(validateForDevice(scanFixture(), supported), []);
  assert(validateForDevice(scanFixture(), { ...supported, maxChannelsPerScanList: 1 }).some(issue => issue.path.endsWith('.channelIds')));
});
