import type { Channel } from './model.ts';
import { createCodeplug } from './model.ts';
import { assertCodeplug } from './validation.ts';
import { formatMHz, parseMHz } from './frequency.ts';

const HEADERS = ['id', 'name', 'rx_mhz', 'tx_mhz', 'bandwidth', 'power', 'rx_ctcss_hz', 'tx_ctcss_hz', 'tx_inhibit'];

// Prefix spreadsheet formulas and literal apostrophes reversibly.
function protect(value: string): string { return /^[=+@\-']/.test(value) ? `'${value}` : value; }
function unprotect(value: string): string { return /^'[=+@\-']/.test(value) ? value.slice(1) : value; }
function quote(value: string): string { return `"${protect(value).replaceAll('"', '""')}"`; }

/** RFC4180 subset: comma or semicolon; BOM, CRLF and quoted fields accepted. */
export function parseCsvRows(source: string, delimiter?: ',' | ';' | '\t', restoreProtection = false): string[][] {
  const text = source.replace(/^\uFEFF/, '');
  let inQuotes = false;
  const counts = new Map<string, number>([[',', 0], [';', 0], ['\t', 0]]);
  for (let index = 0; index < text.length; index++) {
    const char = text[index];
    if (char === '"') { if (inQuotes && text[index + 1] === '"') index++; else inQuotes = !inQuotes; }
    else if (!inQuotes && (char === '\r' || char === '\n')) break;
    else if (!inQuotes && counts.has(char)) counts.set(char, counts.get(char)! + 1);
  }
  const separator = delimiter ?? [...counts].sort((a, b) => b[1] - a[1])[0][0];
  const result: string[][] = [];
  let row: string[] = [], field = '', quoted = false, closed = false;
  for (let index = 0; index < text.length; index++) {
    const char = text[index];
    if (quoted) {
      if (char === '"' && text[index + 1] === '"') { field += '"'; index++; }
      else if (char === '"') { quoted = false; closed = true; }
      else field += char;
    } else if (char === '"') {
      if (field || closed) throw new Error('CSV : guillemet inattendu.');
      quoted = true;
    } else if (char === separator || char === '\n' || char === '\r') {
      row.push(restoreProtection ? unprotect(field) : field); field = ''; closed = false;
      if (char !== separator) {
        if (row.some(value => value !== '')) result.push(row);
        row = [];
        if (char === '\r' && text[index + 1] === '\n') index++;
      }
    } else {
      if (closed) throw new Error('CSV : caractère après fermeture des guillemets.');
      field += char;
    }
  }
  if (quoted) throw new Error('CSV : guillemets non fermés.');
  row.push(restoreProtection ? unprotect(field) : field);
  if (row.some(value => value !== '')) result.push(row);
  return result;
}

function tone(source: string): number | null {
  if (!source) return null;
  if (!/^\d+(?:[.,]\d)?$/.test(source)) throw new Error('CTCSS : entier ou une décimale en Hz attendu.');
  const [whole, fraction = '0'] = source.split(/[.,]/);
  return Number(whole) * 10 + Number(fraction);
}

export function parseChannelsCsv(source: string): Channel[] {
  const [header, ...data] = parseCsvRows(source, undefined, true);
  if (!header || header.join(',') !== HEADERS.join(',')) throw new Error(`En-tête CSV attendu : ${HEADERS.join(',')}`);
  const channels = data.map((row, index): Channel => {
    try {
      if (row.length !== HEADERS.length) throw new Error('Nombre de colonnes incorrect.');
      const [id, name, rx, tx, bandwidth, power, rxTone, txTone, inhibit] = row;
      if (!['true', 'false'].includes(inhibit)) throw new Error('tx_inhibit doit être true ou false.');
      if (!['narrow', 'wide'].includes(bandwidth)) throw new Error('bandwidth doit être narrow ou wide.');
      return { id, name, mode: 'FM', rxHz: parseMHz(rx), txHz: parseMHz(tx),
        bandwidth: bandwidth as Channel['bandwidth'], power, rxCtcssDeciHz: tone(rxTone),
        txCtcssDeciHz: tone(txTone), txInhibit: inhibit === 'true' };
    } catch (error) { throw new Error(`CSV, enregistrement ${index + 2} : ${(error as Error).message}`); }
  });
  assertCodeplug({ ...createCodeplug(), channels });
  return channels;
}

export function isOpenD578Csv(source: string): boolean {
  try { return parseCsvRows(source)[0]?.join(',') === HEADERS.join(','); }
  catch { return false; }
}

export function serializeChannelsCsv(channels: Channel[]): string {
  assertCodeplug({ ...createCodeplug(), channels });
  const toneText = (value: number | null): string => value === null ? '' : (value / 10).toFixed(1);
  return [HEADERS.join(','), ...channels.map(channel => [
    channel.id, channel.name, formatMHz(channel.rxHz), formatMHz(channel.txHz),
    channel.bandwidth, channel.power, toneText(channel.rxCtcssDeciHz), toneText(channel.txCtcssDeciHz),
    String(channel.txInhibit),
  ].map(quote).join(','))].join('\r\n') + '\r\n';
}
