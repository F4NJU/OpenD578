/** D578 V1.21 channel profile. Sources and qualification: docs/cps/OEM_GLOBAL_READ.md. */
export const OEM_CAPACITY = 4000;
export const OEM_BITMAP = 0x024c1500;
export const OEM_BITMAP_BYTES = 512;
export type OemTone = { kind: 'none' } | { kind: 'ctcss'; deciHz: number } |
  { kind: 'dcs'; code: string; inverted: boolean } | { kind: 'unknown'; rawMode: number; rawValue: number };
const OEM_CTCSS = [625,670,693,719,744,770,797,825,854,885,915,948,974,1000,1035,1072,1109,1148,1188,1230,1273,1318,1365,1413,1462,1514,1567,1598,1622,1655,1679,1713,1738,1773,1799,1835,1862,1899,1928,1966,1995,2035,2065,2107,2181,2257,2291,2336,2418,2503,2541];
export function oemChannelAddress(slot: number): number {
  if (!Number.isInteger(slot) || slot < 1 || slot > OEM_CAPACITY) throw new Error('Emplacement OEM hors limites.');
  const index = slot - 1;
  return 0x00800000 + Math.floor(index / 128) * 0x40000 + index % 128 * 64;
}
export function oemReadableAddress(address: number): boolean {
  if (!Number.isInteger(address) || address % 16) return false;
  if (address >= OEM_BITMAP && address < OEM_BITMAP + OEM_BITMAP_BYTES) return true;
  const relative = address - 0x00800000, bank = Math.floor(relative / 0x40000), offset = relative % 0x40000;
  return relative >= 0 && bank < 32 && offset >= 0 && offset < (bank === 31 ? 32 : 128) * 64;
}
export function oemActiveSlots(bitmap: Uint8Array): number[] {
  if (bitmap.length !== OEM_BITMAP_BYTES) throw new Error('Bitmap des canaux incomplet.');
  return Array.from({ length: OEM_CAPACITY }, (_, i) => i).filter(i => Boolean(bitmap[i >> 3] & (1 << (i % 8)))).map(i => i + 1);
}
export function decodeOemTone(record: Uint8Array, direction: 'rx' | 'tx'): OemTone {
  if (record.length !== 64) throw new Error('Canal OEM incomplet.');
  const mode = (record[9] >> (direction === 'rx' ? 0 : 2)) & 3;
  const index = record[direction === 'rx' ? 11 : 10];
  if (mode === 0) return { kind: 'none' };
  if (mode === 1) {
    const deciHz = index === 51 ? record[16] + record[17] * 256 : OEM_CTCSS[index];
    if (Number.isInteger(deciHz) && deciHz >= 600 && deciHz <= 2600) return { kind: 'ctcss', deciHz };
  }
  const at = direction === 'rx' ? 14 : 12, word = record[at] + record[at + 1] * 256;
  if (mode === 2 && word < 1024) return { kind: 'dcs', code: (word & 511).toString(8).padStart(3, '0'), inverted: word >= 512 };
  return { kind: 'unknown', rawMode: mode, rawValue: mode === 1 ? index : word };
}
export function formatOemTone(tone: OemTone | undefined): string {
  if (!tone || tone.kind === 'unknown') return 'Inconnu';
  if (tone.kind === 'none') return 'Aucune';
  if (tone.kind === 'ctcss') return `${(tone.deciHz / 10).toFixed(1)} Hz`;
  return `D${tone.code}${tone.inverted ? 'I' : 'N'}`;
}
