import test from 'node:test';
import assert from 'node:assert/strict';
import { createCodeplug } from '../src/core/model.ts';
import { EditorHistory } from '../src/core/editor.ts';
import { parseCsvRows, parseChannelsCsv, serializeChannelsCsv, isOpenD578Csv } from '../src/core/csv.ts';
import { readCsvTable, suggestCsvMapping, previewCsvImport, applyCsvImport } from '../src/core/csv-mapping.ts';
import type { CsvImportOptions } from '../src/core/csv-mapping.ts';

function config(source: string): { table: ReturnType<typeof readCsvTable>; options: CsvImportOptions } {
  const table = readCsvTable(source);
  return { table, options: { mapping: suggestCsvMapping(table.headers), frequencyUnit: 'MHz', offsetUnit: 'MHz', offsetDirection: 'minus', power: 'low', bandwidth: 'narrow', txInhibit: true } };
}

test('CSV separator detection ignores quoted punctuation and supports tabs and multiline fields', () => {
  assert.deepEqual(parseCsvRows('"name;alias",rx\r\n"Relais, \\"été\\"",145.5'.replaceAll('\\"', '""')), [['name;alias', 'rx'], ['Relais, "été"', '145.5']]);
  assert.deepEqual(parseCsvRows('Name\tRX\n"A\nB"\t145.5'), [['Name', 'RX'], ['A\nB', '145.5']]);
  assert.deepEqual(parseCsvRows("Name;RX\n'=name;145.5"), [['Name', 'RX'], ["'=name", '145.5']]);
  assert.throws(() => readCsvTable('one-column\nvalue'));
  assert.throws(() => parseCsvRows('Name,RX\n"not closed,145.5'));
  assert.equal(isOpenD578Csv('Name,RX\n"not closed,145.5'), false);
  assert.throws(() => readCsvTable(Array.from({ length: 257 }, (_, index) => `column${index}`).join(',')));
});

test('mapping suggestions do not choose between ambiguous duplicate headers', () => {
  const mapping = suggestCsvMapping(['Nom', 'Réception', 'RX', 'TX', 'DCS']);
  assert.equal(mapping.name, 0); assert.equal(mapping.rx, null); assert.equal(mapping.tx, 3);
  assert.equal(mapping.rxTone, null);
});

test('mapped import handles decimal commas, independent tones, custom power and reception-only defaults', () => {
  const { table, options } = config('Nom;RX;Décalage;CTCSS RX;CTCSS TX;Puissance\nRelais été;145,600001;-0,600000;123,0;88,5;association');
  const row = previewCsvImport(table, options, createCodeplug())[0];
  assert.deepEqual(row.errors, []); assert.equal(row.channel?.rxHz, 145600001); assert.equal(row.channel?.txHz, 145000001);
  assert.equal(row.channel?.rxCtcssDeciHz, 1230); assert.equal(row.channel?.txCtcssDeciHz, 885);
  assert.equal(row.channel?.power, 'association'); assert.equal(row.channel?.txInhibit, true);
});

test('frequency and offset units are explicit and preserve exact Hz', () => {
  const { table, options } = config('Name,RX,offset\nA,145600001,-600');
  options.frequencyUnit = 'Hz'; options.offsetUnit = 'kHz';
  assert.equal(previewCsvImport(table, options, createCodeplug())[0].channel?.txHz, 145000001);
  const other = config('Name,RX\nB,145500.001'); other.options.frequencyUnit = 'kHz';
  assert.equal(previewCsvImport(other.table, other.options, createCodeplug())[0].channel?.rxHz, 145500001);
  const bad = config('Name,RX\nB,145500000.1'); bad.options.frequencyUnit = 'Hz';
  assert(previewCsvImport(bad.table, bad.options, createCodeplug())[0].errors.length);
});

test('inconsistent TX, signed shift, DMR, DCS, bad booleans and malformed rows are errors without partial channels', () => {
  for (const source of [
    'Name,RX,TX,offset\nA,145.6,145.5,-0.6',
    'Name,RX,offset,direction\nA,145.6,-0.6,+',
    'Name,RX,offset,direction\nA,145.6,0.6,simplex',
    'Name,RX,direction\nA,145.6,+',
    'Name,RX,Mode\nA,145.5,DMR',
    'Name,RX,Mode,bandwidth\nA,145.5,NFM,25',
    'Name,RX,txTone\nA,145.5,D023N',
    'Name,RX,rxOnly\nA,145.5,perhaps',
    'Name,RX\nA,145.5,extra', 'Name,RX\n,145.5',
    'Name,RX,offset\nA,0.1,-0.6',
  ]) {
    const { table, options } = config(source), row = previewCsvImport(table, options, createCodeplug())[0];
    assert.equal(row.channel, null, source); assert(row.errors.length, source);
  }
});

test('TX mapping, NFM, width and explicit RX/TX flags are retained', () => {
  const { table, options } = config('Name,RX,TX,Mode,rxOnly,bandwidth\nA,145.5,145.6,FM,false,25\nB,433.5,,NFM,oui,');
  const rows = previewCsvImport(table, options, createCodeplug());
  assert.equal(rows[0].channel?.txHz, 145600000); assert.equal(rows[0].channel?.txInhibit, false); assert.equal(rows[0].channel?.bandwidth, 'wide');
  assert.equal(rows[1].channel?.bandwidth, 'narrow'); assert.equal(rows[1].channel?.txHz, 433500000);
});

test('preview detects duplicates in current document and earlier valid records', () => {
  const { table, options } = config('Name,RX\nA,145.5\nB,145.5\nA,433.5');
  const first = previewCsvImport(table, options, createCodeplug());
  assert.equal(first[0].duplicates.length, 0); assert(first[1].duplicates.length); assert(first[2].duplicates.length);
  const current = { ...createCodeplug(), channels: [first[0].channel!] };
  assert(previewCsvImport(table, options, current)[0].duplicates.length >= 2);
});

test('selected import is atomic, preserves other data, adds fresh IDs and zone members, and undoes once', () => {
  const { table, options } = config('Name,RX\nA,145.5\nInvalid,wrong\nB,433.5');
  const current = { ...createCodeplug(), zones: [{ id: 'zone', name: 'Zone', channelIds: [] as string[] }] }, before = structuredClone(current);
  const rows = previewCsvImport(table, options, current); let sequence = 0;
  assert.throws(() => applyCsvImport(current, rows, [2, 3], 'zone', () => `new-${++sequence}`));
  assert.deepEqual(current, before);
  const history = new EditorHistory(current);
  history.commit(applyCsvImport(current, rows, [2, 4], 'zone', () => `new-${++sequence}`));
  assert.equal(history.value.channels.length, 2);
  assert.deepEqual(history.value.zones[0].channelIds, history.value.channels.map(channel => channel.id));
  assert.deepEqual(history.value.scanLists, current.scanLists); history.undo(); assert.deepEqual(history.value, before);
  assert.throws(() => applyCsvImport(current, rows, [], null, () => 'same'));
  assert.throws(() => applyCsvImport(current, rows, [2, 2], null, () => 'same'));
  assert.throws(() => applyCsvImport(current, rows, [2, 4], null, () => 'same'));
  assert.throws(() => applyCsvImport(current, rows, [2], 'absent', () => 'new'));
});

test('mapping errors fail before preview, and native CSV still round-trips protected names', () => {
  const { table, options } = config('Label,Frequency\nA,145.5'); options.mapping.name = null;
  assert.throws(() => previewCsvImport(table, options, createCodeplug()));
  options.mapping.name = 0; options.mapping.rx = 99;
  assert.throws(() => previewCsvImport(table, options, createCodeplug()));
  const nativeConfig = config('Name,RX\n=Relais,145.5'), channel = previewCsvImport(nativeConfig.table, nativeConfig.options, createCodeplug())[0].channel!;
  const csv = serializeChannelsCsv([channel]); assert(isOpenD578Csv(csv)); assert.deepEqual(parseChannelsCsv(csv), [channel]);
});
