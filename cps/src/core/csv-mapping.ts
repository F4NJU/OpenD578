import type { Channel, Codeplug } from './model.ts';
import { createCodeplug } from './model.ts';
import { assertCodeplug, validateCodeplug } from './validation.ts';
import { parseMHz } from './frequency.ts';
import { parseCsvRows } from './csv.ts';

export const CSV_FIELDS = ['name', 'rx', 'tx', 'offset', 'direction', 'rxTone', 'txTone', 'power', 'bandwidth', 'mode', 'inhibit'] as const;
export type CsvField = typeof CSV_FIELDS[number];
export type CsvMapping = Record<CsvField, number | null>;
export interface CsvImportOptions {
  mapping: CsvMapping;
  frequencyUnit: 'MHz' | 'kHz' | 'Hz';
  offsetUnit: 'MHz' | 'kHz' | 'Hz';
  offsetDirection: 'plus' | 'minus';
  power: string;
  bandwidth: 'narrow' | 'wide';
  txInhibit: boolean;
}
export interface CsvTable { headers: string[]; data: string[][] }
export interface CsvPreviewRow { record: number; channel: Channel | null; errors: string[]; duplicates: string[] }
function normalHeader(value: string): string { return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]/g, ''); }
const ALIASES: Record<CsvField, string[]> = {
  name: ['name', 'nom', 'channelname', 'nomducanal', 'nomcanal', 'canal'],
  rx: ['rx', 'rxmhz', 'rxfrequency', 'receivefrequency', 'frequencerx', 'reception', 'frequency', 'frequence'],
  tx: ['tx', 'txmhz', 'txfrequency', 'transmitfrequency', 'frequencetx', 'emission'],
  offset: ['offset', 'shift', 'decalage', 'offsetmhz'], direction: ['direction', 'sens', 'duplex'],
  rxTone: ['rxctcsshz', 'rxctcss', 'ctcssrx', 'rxtone', 'decodage'],
  txTone: ['txctcsshz', 'txctcss', 'ctcsstx', 'txtone', 'encodage', 'tone'],
  power: ['power', 'puissance'], bandwidth: ['bandwidth', 'largeur', 'largeurfm'],
  mode: ['mode', 'channelmode'], inhibit: ['txinhibit', 'rxonly', 'rxseul', 'interdictiontx'],
};
/** Guesses are editable suggestions, never a claim of compatibility with another CPS. */
export function suggestCsvMapping(headers: string[]): CsvMapping {
  return Object.fromEntries(CSV_FIELDS.map(field => {
    const matches = headers.map((header, index) => ALIASES[field].includes(normalHeader(header)) ? index : -1).filter(index => index >= 0);
    return [field, matches.length === 1 ? matches[0] : null];
  })) as CsvMapping;
}
export function readCsvTable(source: string, delimiter?: ',' | ';' | '\t'): CsvTable {
  const [headers, ...data] = parseCsvRows(source, delimiter);
  if (!headers || headers.length < 2) throw new Error('Au moins deux colonnes et une ligne d’en-tête sont nécessaires.');
  if (headers.length > 256) throw new Error('Maximum 256 colonnes par import externe.');
  if (data.length > 10000) throw new Error('Maximum 10 000 enregistrements par import.');
  return { headers, data };
}
function amountHz(source: string, unit: CsvImportOptions['frequencyUnit'], allowZero = false): number {
  const value = source.trim().replace(',', '.');
  if (!/^\d+(?:\.\d+)?$/.test(value)) throw new Error('Fréquence/décalage numérique attendu, sans unité ni exposant.');
  let hz: number;
  if (unit === 'MHz') hz = /^0+(?:\.0{1,6})?$/.test(value) && allowZero ? 0 : parseMHz(value);
  else {
    const digits = unit === 'kHz' ? 3 : unit === 'Hz' ? 0 : -1;
    if (digits < 0 || (value.split('.')[1]?.length ?? 0) > digits) throw new Error('Précision incompatible avec l’unité choisie.');
    const [whole, fraction = ''] = value.split('.');
    hz = Number(whole) * 10 ** digits + Number(fraction.padEnd(digits, '0'));
  }
  if (!Number.isSafeInteger(hz) || hz < 0 || (!allowZero && hz === 0)) throw new Error('Fréquence entière positive en Hz attendue.');
  return hz;
}
function mappedTone(value: string): number | null {
  if (!value || /^(?:off|none|aucun|desactive|désactivé|0)$/i.test(value)) return null;
  if (!/^\d+(?:[.,]\d)?$/.test(value)) throw new Error('CTCSS en Hz attendu (DCS non pris en charge).');
  const [whole, fraction = '0'] = value.split(/[.,]/);
  const tone = Number(whole) * 10 + Number(fraction);
  return tone === 0 ? null : tone;
}
function mappedBoolean(value: string): boolean {
  if (/^(true|1|yes|oui)$/i.test(value)) return true;
  if (/^(false|0|no|non)$/i.test(value)) return false;
  throw new Error('RX seul : true/false, oui/non ou 1/0 attendu.');
}
function mappedWidth(value: string): 'narrow' | 'wide' {
  if (/^(narrow|nfm|etroite|étroite|12[.,]5(?:\s*khz)?)$/i.test(value)) return 'narrow';
  if (/^(wide|large|25(?:\s*khz)?)$/i.test(value)) return 'wide';
  throw new Error('Largeur FM inconnue : narrow/12.5 ou wide/25 attendu.');
}
function checkMapping(table: CsvTable, options: CsvImportOptions): void {
  for (const field of CSV_FIELDS) {
    const index = options.mapping[field];
    if (index !== null && (!Number.isInteger(index) || index < 0 || index >= table.headers.length)) throw new Error(`Colonne invalide : ${field}.`);
  }
  if (options.mapping.name === null || options.mapping.rx === null) throw new Error('Associez au minimum le nom et la fréquence RX.');
  if (!['MHz', 'kHz', 'Hz'].includes(options.frequencyUnit) || !['MHz', 'kHz', 'Hz'].includes(options.offsetUnit)) throw new Error('Unité inconnue.');
  if (!['plus', 'minus'].includes(options.offsetDirection)) throw new Error('Sens par défaut inconnu.');
}
function mappedChannel(row: string[], record: number, options: CsvImportOptions): Channel {
  const get = (field: CsvField): string => options.mapping[field] === null ? '' : row[options.mapping[field]!].trim();
  const rxHz = amountHz(get('rx'), options.frequencyUnit);
  const mode = get('mode');
  if (mode && !/^(fm|nfm|analog|analogique)$/i.test(mode)) throw new Error(`Mode non pris en charge : ${mode}. Seuls les canaux analogiques FM sont importables.`);
  const bandwidth = get('bandwidth') ? mappedWidth(get('bandwidth')) : /^nfm$/i.test(mode) ? 'narrow' : options.bandwidth;
  if (/^nfm$/i.test(mode) && bandwidth !== 'narrow') throw new Error('Mode NFM et largeur large contradictoires.');
  let txHz = rxHz;
  const offset = get('offset'), direction = get('direction');
  if (direction && !/^(\+|-|plus|minus|simplex)$/i.test(direction)) throw new Error('Sens du décalage inconnu.');
  if (direction && !offset && !/^simplex$/i.test(direction)) throw new Error('Sens indiqué sans valeur de décalage.');
  if (offset) {
    const sign = offset.startsWith('-') ? -1 : offset.startsWith('+') ? 1 : null;
    const magnitude = amountHz(offset.replace(/^[+-]/, ''), options.offsetUnit, true);
    const explicit = /^(\+|plus)$/i.test(direction) ? 1 : /^(-|minus)$/i.test(direction) ? -1 : null;
    if (sign !== null && explicit !== null && sign !== explicit && magnitude !== 0) throw new Error('Sens et décalage signé contradictoires.');
    if (/^simplex$/i.test(direction) && magnitude !== 0) throw new Error('Simplex avec décalage non nul.');
    txHz = rxHz + magnitude * (sign ?? explicit ?? (options.offsetDirection === 'plus' ? 1 : -1));
  }
  const tx = get('tx');
  if (tx) {
    const explicitTx = amountHz(tx, options.frequencyUnit);
    if ((offset || /^simplex$/i.test(direction)) && explicitTx !== txHz) throw new Error('TX et décalage ne donnent pas la même fréquence.');
    txHz = explicitTx;
  }
  return { id: `csv-preview-${record}`, name: get('name'), mode: 'FM', rxHz, txHz,
    rxCtcssDeciHz: mappedTone(get('rxTone')), txCtcssDeciHz: mappedTone(get('txTone')),
    power: get('power') || options.power, bandwidth,
    txInhibit: get('inhibit') ? mappedBoolean(get('inhibit')) : options.txInhibit };
}
function pairKey(channel: Channel): string { return `${channel.rxHz}:${channel.txHz}:${channel.rxCtcssDeciHz}:${channel.txCtcssDeciHz}`; }
function nameKey(channel: Channel): string { return channel.name.trim().normalize('NFC').toLocaleLowerCase('fr'); }
export function previewCsvImport(table: CsvTable, options: CsvImportOptions, current: Codeplug): CsvPreviewRow[] {
  assertCodeplug(current); checkMapping(table, options);
  const names = new Set(current.channels.map(nameKey)), pairs = new Set(current.channels.map(pairKey));
  return table.data.map((row, index) => {
    const record = index + 2;
    try {
      if (row.length !== table.headers.length) throw new Error('Nombre de colonnes différent de l’en-tête.');
      const channel = mappedChannel(row, record, options);
      const errors = validateCodeplug({ ...createCodeplug(), channels: [channel] });
      if (errors.length) throw new Error(errors.map(error => error.message).join(' '));
      const duplicates: string[] = [];
      if (names.has(nameKey(channel))) duplicates.push('Nom déjà présent dans le document ou une ligne précédente');
      if (pairs.has(pairKey(channel))) duplicates.push('Fréquences et tons déjà présents dans le document ou une ligne précédente');
      names.add(nameKey(channel)); pairs.add(pairKey(channel));
      return { record, channel, errors: [], duplicates };
    } catch (error) { return { record, channel: null, errors: [(error as Error).message], duplicates: [] }; }
  });
}
export function applyCsvImport(current: Codeplug, preview: CsvPreviewRow[], records: number[], zoneId: string | null, makeId: () => string): Codeplug {
  assertCodeplug(current);
  if (!records.length || new Set(records).size !== records.length) throw new Error('Sélectionnez au moins une ligne valide, sans répétition.');
  if (zoneId && !current.zones.some(zone => zone.id === zoneId)) throw new Error('Zone de destination absente.');
  const rows = new Map(preview.map(row => [row.record, row]));
  const channels = records.map(record => {
    const row = rows.get(record);
    if (!row?.channel || row.errors.length) throw new Error(`Enregistrement ${record} invalide ou absent.`);
    return { ...row.channel, id: makeId() };
  });
  const next = { ...current, channels: [...current.channels, ...channels],
    zones: current.zones.map(zone => zone.id !== zoneId ? zone : { ...zone, channelIds: [...zone.channelIds, ...channels.map(channel => channel.id)] }) };
  assertCodeplug(next); return next;
}
