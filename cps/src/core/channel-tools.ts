import type { Channel, Codeplug, ValidationIssue } from './model.ts';
import { assertCodeplug, validateCodeplug } from './validation.ts';

export function txFromOffset(rxHz: number, direction: 'simplex' | 'plus' | 'minus', offsetHz = 0): number {
  if (!Number.isSafeInteger(rxHz) || rxHz <= 0 || !Number.isSafeInteger(offsetHz) || offsetHz < 0) throw new Error('Fréquences et décalage entiers en Hz attendus.');
  if (!['simplex', 'plus', 'minus'].includes(direction)) throw new Error('Sens du décalage inconnu.');
  const tx = direction === 'simplex' ? rxHz : rxHz + (direction === 'plus' ? offsetHz : -offsetHz);
  if (!Number.isSafeInteger(tx) || tx <= 0) throw new Error('Le décalage produit une fréquence TX invalide.');
  return tx;
}

/** The first new channel is one step after the template. One atomic editor action. */
export function createChannelSeries(value: Codeplug, templateId: string, count: number, stepHz: number, makeId: () => string, zoneId: string | null = null): Codeplug {
  assertCodeplug(value);
  if (!Number.isInteger(count) || count < 1 || count > 256) throw new Error('La série doit contenir entre 1 et 256 nouveaux canaux.');
  if (!Number.isSafeInteger(stepHz) || stepHz === 0) throw new Error('Pas non nul entier en Hz attendu.');
  const template = value.channels.find(channel => channel.id === templateId);
  if (!template) throw new Error('Sélectionnez un canal modèle.');
  if (zoneId && !value.zones.some(zone => zone.id === zoneId)) throw new Error('Zone de destination absente.');
  const channels: Channel[] = Array.from({ length: count }, (_, index) => ({ ...template,
    id: makeId(), name: `${template.name} ${String(index + 1).padStart(2, '0')}`,
    rxHz: template.rxHz + (index + 1) * stepHz, txHz: template.txHz + (index + 1) * stepHz,
  }));
  const next = { ...value, channels: [...value.channels, ...channels], zones: value.zones.map(zone => zone.id !== zoneId ? zone : { ...zone, channelIds: [...zone.channelIds, ...channels.map(channel => channel.id)] }) };
  assertCodeplug(next);
  return next;
}

export interface DocumentFinding extends ValidationIssue { severity: 'error' | 'warning' }
export function reviewCodeplug(value: unknown): DocumentFinding[] {
  const errors = validateCodeplug(value);
  if (errors.length) return errors.map(error => ({ ...error, severity: 'error' }));
  const document = value as Codeplug, findings: DocumentFinding[] = [];
  const warn = (path: string, code: string, message: string): void => { findings.push({ path, code, message, severity: 'warning' }); };
  if (!document.channels.length) warn('$.channels', 'empty_document', 'Le document ne contient aucun canal.');
  const names = new Set<string>(), pairs = new Set<string>();
  document.channels.forEach((channel, index) => {
    const name = channel.name.trim().normalize('NFC').toLocaleLowerCase('fr');
    if (names.has(name)) warn(`$.channels[${index}].name`, 'duplicate_name', `Nom déjà utilisé : ${channel.name}.`);
    names.add(name);
    const pair = `${channel.rxHz}:${channel.txHz}:${channel.rxCtcssDeciHz}:${channel.txCtcssDeciHz}`;
    if (pairs.has(pair)) warn(`$.channels[${index}]`, 'duplicate_frequencies', `${channel.name} : fréquences et tons déjà présents sur un autre canal. Ce choix peut être volontaire.`);
    pairs.add(pair);
  });
  for (const collection of ['zones', 'scanLists'] as const) document[collection].forEach((list, index) => {
    if (!list.channelIds.length) warn(`$.${collection}[${index}].channelIds`, 'empty_list', `Liste vide : ${list.name}.`);
  });
  return findings;
}
