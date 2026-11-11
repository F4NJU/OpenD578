import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createCodeplug } from '../src/core/model.ts';
import type { Codeplug, DeviceCapabilities } from '../src/core/model.ts';
import { validateCodeplug, CodeplugValidationError } from '../src/core/validation.ts';
import { parseCodeplug, serializeCodeplug } from '../src/core/json.ts';
import { validateForDevice } from '../src/core/capabilities.ts';
import { parseMHz, formatMHz } from '../src/core/frequency.ts';

function fixture(): Codeplug {
  return parseCodeplug(readFileSync(new URL('../examples/analog.opend578.json', import.meta.url), 'utf8'));
}

// Deliberately synthetic. These values do not describe an AT-D578's capabilities.
const capabilities: DeviceCapabilities = {
  maxChannels: 2, maxZones: 1, maxChannelsPerZone: 2, maxNameBytes: 16,
  rxBands: [{ minHz: 144000000, maxHz: 146000000 }],
  txBands: [{ minHz: 144000000, maxHz: 146000000 }],
  bandwidths: ['narrow', 'wide'], powerLevels: ['low'],
  ctcssDeciHz: [885, 1230], supportsVfo: true,
};

test('empty and example codeplugs round-trip exactly without mutating the source', () => {
  for (const value of [createCodeplug(), fixture()]) {
    const before = structuredClone(value);
    assert.deepEqual(parseCodeplug(serializeCodeplug(value)), value);
    assert.deepEqual(value, before);
  }
});

test('reordering channels preserves zone membership and separate RX/TX tones', () => {
  const value = fixture();
  const reordered = { ...value, channels: [...value.channels].reverse() };
  const loaded = parseCodeplug(serializeCodeplug(reordered));
  assert.deepEqual(loaded.zones, value.zones);
  const repeater = loaded.channels.find(channel => channel.id === 'repeater-demo');
  assert.equal(repeater?.rxCtcssDeciHz, 1230);
  assert.equal(repeater?.txCtcssDeciHz, 885);
});

test('malformed JSON and unsupported versions produce actionable validation errors', () => {
  assert.throws(() => parseCodeplug('{'), CodeplugValidationError);
  for (const value of [null, [], 42, {}, { ...fixture(), schemaVersion: 2 }]) {
    assert.throws(() => parseCodeplug(JSON.stringify(value)), CodeplugValidationError);
  }
});

test('unknown fields including calibration are rejected at every object level', () => {
  for (const change of [
    (value: Codeplug) => Object.assign(value, { calibration: {} }),
    (value: Codeplug) => Object.assign(value.channels[0], { oemAddress: 123 }),
    (value: Codeplug) => Object.assign(value.zones[0], { futureSetting: true }),
    (value: Codeplug) => Object.assign(value.vfo!, { futureSetting: true }),
  ]) {
    const value = fixture();
    change(value);
    assert(validateCodeplug(value).some(issue => issue.code === 'unknown_field'));
    assert.throws(() => serializeCodeplug(value), CodeplugValidationError);
  }
});

test('invalid channel values fail validation without coercion', () => {
  for (const [field, bad] of [
    ['rxHz', '145500000'], ['txHz', -1], ['rxHz', 145500000.5],
    ['rxHz', Number.NaN], ['txHz', Number.POSITIVE_INFINITY],
    ['txHz', Number.MAX_SAFE_INTEGER + 1], ['bandwidth', 'auto'],
    ['mode', 'DMR'], ['power', ''], ['txInhibit', 1],
    ['rxCtcssDeciHz', 88.5], ['txCtcssDeciHz', 0],
    ['name', '  '], ['name', 'bad\nname'], ['name', '\ud800'], ['id', '../x'],
  ] as const) {
    const value = fixture();
    Object.assign(value.channels[0], { [field]: bad });
    assert(validateCodeplug(value).some(issue => issue.path === `$.channels[0].${field}`), field);
  }
});

test('missing fields, duplicate IDs and broken zone references are rejected', () => {
  const missing = fixture();
  Reflect.deleteProperty(missing.channels[0], 'txInhibit');
  assert(validateCodeplug(missing).some(issue => issue.code === 'missing_field'));
  const duplicate = fixture();
  duplicate.channels[1].id = duplicate.channels[0].id;
  assert(validateCodeplug(duplicate).some(issue => issue.code === 'duplicate_id'));
  const broken = fixture();
  broken.zones[0].channelIds = ['absent', 'absent'];
  const issues = validateCodeplug(broken);
  assert(issues.some(issue => issue.code === 'missing_channel'));
  assert(issues.some(issue => issue.code === 'duplicate_id'));
});

test('sparse arrays supplied by callers cannot serialize into invalid null records', () => {
  for (const mutate of [
    (value: Codeplug) => { value.channels.length += 1; },
    (value: Codeplug) => { value.zones.length += 1; },
    (value: Codeplug) => { value.zones[0].channelIds.length += 1; },
  ]) {
    const value = fixture();
    mutate(value);
    assert.throws(() => serializeCodeplug(value), CodeplugValidationError);
  }
});

test('synthetic capabilities enforce capacity, names, bands and settings', () => {
  assert.deepEqual(validateForDevice(fixture(), capabilities), []);
  const value = fixture();
  Object.assign(value.channels[0], { name: 'é'.repeat(9), rxHz: 433500000, txHz: 433500000,
    power: 'turbo', bandwidth: 'wide', rxCtcssDeciHz: 1000, txInhibit: false });
  const limited = { ...capabilities, maxChannels: 0, maxZones: 0, maxChannelsPerZone: 0,
    bandwidths: [] as DeviceCapabilities['bandwidths'], supportsVfo: false };
  const paths = validateForDevice(value, limited).map(issue => issue.path);
  for (const path of ['$.channels', '$.zones', '$.zones[0].channelIds', '$.vfo',
    '$.channels[0].name', '$.channels[0].rxHz', '$.channels[0].txHz',
    '$.channels[0].power', '$.channels[0].bandwidth', '$.channels[0].rxCtcssDeciHz']) {
    assert(paths.includes(path), path);
  }
});

test('TX-inhibited channels still validate RX but do not require a usable TX band', () => {
  const value = fixture();
  Object.assign(value.channels[0], { txHz: 433500000, txInhibit: true });
  assert.deepEqual(validateForDevice(value, capabilities), []);
  value.channels[0].rxHz = 433500000;
  assert(validateForDevice(value, capabilities).some(issue => issue.path.endsWith('.rxHz')));
});

test('MHz conversion preserves individual Hz, accepts French decimal separator and rejects rounding', () => {
  for (const hz of [1, 145500000, 145600001, 439987500, Number.MAX_SAFE_INTEGER]) {
    assert.equal(parseMHz(formatMHz(hz)), hz);
  }
  assert.equal(parseMHz(' 145,600001 '), 145600001);
  for (const source of ['145.0000001', '1e2', '-145', '145 MHz', '', '0', 'Infinity']) {
    assert.throws(() => parseMHz(source), source);
  }
});
