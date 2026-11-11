/** Decimal MHz input with no binary floating-point rounding or exponent syntax. */
export function parseMHz(source: string): number {
  const match = /^(\d+)(?:[.,](\d{1,6}))?$/.exec(source.trim());
  if (!match) throw new Error('Fréquence en MHz attendue, avec au plus 6 décimales.');
  const hz = Number(match[1]) * 1_000_000 + Number((match[2] ?? '').padEnd(6, '0'));
  if (!Number.isSafeInteger(hz) || hz <= 0) throw new Error('Fréquence entière positive en Hz attendue.');
  return hz;
}

export function formatMHz(hz: number): string {
  if (!Number.isSafeInteger(hz) || hz <= 0) throw new Error('Fréquence entière positive en Hz attendue.');
  return `${Math.floor(hz / 1_000_000)}.${String(hz % 1_000_000).padStart(6, '0')}`;
}
