import type { Codeplug, ValidationIssue } from './model.ts';

type RecordValue = Record<string, unknown>;
type Issues = ValidationIssue[];
const ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/;
const CONTROL_CHARACTERS = /[\u0000-\u001f\u007f-\u009f]/u;
const SETTINGS_KEYS = [
  'mode', 'rxHz', 'txHz', 'bandwidth', 'power',
  'rxCtcssDeciHz', 'txCtcssDeciHz', 'txInhibit',
];

function issue(issues: Issues, path: string, code: string, message: string): void {
  issues.push({ path, code, message });
}

function record(value: unknown, path: string, keys: string[], issues: Issues): value is RecordValue {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    issue(issues, path, 'object', 'Objet attendu.');
    return false;
  }
  for (const key of Object.keys(value)) {
    if (!keys.includes(key)) issue(issues, `${path}.${key}`, 'unknown_field', 'Champ inconnu : aucune suppression implicite.');
  }
  for (const key of keys) {
    if (!Object.hasOwn(value, key)) issue(issues, `${path}.${key}`, 'missing_field', 'Champ obligatoire.');
  }
  return true;
}

function text(value: unknown, path: string, issues: Issues): void {
  if (typeof value !== 'string' || !value.trim() || CONTROL_CHARACTERS.test(value) || !value.isWellFormed()) {
    issue(issues, path, 'text', 'Texte non vide, Unicode valide et sans caractère de contrôle attendu.');
  }
}

function identifier(value: unknown, path: string, seen: Set<string>, issues: Issues): void {
  if (typeof value !== 'string' || !ID_PATTERN.test(value)) {
    issue(issues, path, 'id', 'Identifiant ASCII de 1 à 64 caractères : lettres, chiffres, tiret ou souligné.');
  } else if (seen.has(value)) {
    issue(issues, path, 'duplicate_id', 'Identifiant déjà utilisé dans cette collection.');
  } else {
    seen.add(value);
  }
}

function settings(value: RecordValue, path: string, issues: Issues): void {
  if (value.mode !== 'FM') issue(issues, `${path}.mode`, 'mode', 'Seul le mode FM est défini en version 1.');
  for (const field of ['rxHz', 'txHz']) {
    const frequency = value[field];
    if (typeof frequency !== 'number' || !Number.isSafeInteger(frequency) || frequency <= 0) {
      issue(issues, `${path}.${field}`, 'frequency', 'Fréquence entière positive en Hz attendue.');
    }
  }
  if (value.bandwidth !== 'narrow' && value.bandwidth !== 'wide') {
    issue(issues, `${path}.bandwidth`, 'bandwidth', 'Valeur narrow ou wide attendue.');
  }
  text(value.power, `${path}.power`, issues);
  for (const field of ['rxCtcssDeciHz', 'txCtcssDeciHz']) {
    const tone = value[field];
    if (tone !== null && (typeof tone !== 'number' || !Number.isSafeInteger(tone) || tone <= 0)) {
      issue(issues, `${path}.${field}`, 'ctcss', 'CTCSS entier positif en dixièmes de Hz, ou null pour désactivé.');
    }
  }
  if (typeof value.txInhibit !== 'boolean') issue(issues, `${path}.txInhibit`, 'boolean', 'Booléen attendu.');
}

function channels(value: unknown, issues: Issues): Set<string> {
  const ids = new Set<string>();
  if (!Array.isArray(value)) {
    issue(issues, '$.channels', 'array', 'Tableau de canaux attendu.');
    return ids;
  }
  Array.from(value).forEach((channel: unknown, index: number) => {
    const path = `$.channels[${index}]`;
    if (!record(channel, path, ['id', 'name', ...SETTINGS_KEYS], issues)) return;
    identifier(channel.id, `${path}.id`, ids, issues);
    text(channel.name, `${path}.name`, issues);
    settings(channel, path, issues);
  });
  return ids;
}

function zones(value: unknown, channelIds: Set<string>, issues: Issues, scan = false): void {
  const collection = scan ? 'scanLists' : 'zones';
  if (!Array.isArray(value)) {
    issue(issues, `$.${collection}`, 'array', 'Tableau de listes attendu.');
    return;
  }
  const ids = new Set<string>();
  Array.from(value).forEach((zone: unknown, index: number) => {
    const path = `$.${collection}[${index}]`;
    if (!record(zone, path, ['id', 'name', 'channelIds', ...(scan ? ['priorityChannelId'] : [])], issues)) return;
    identifier(zone.id, `${path}.id`, ids, issues);
    text(zone.name, `${path}.name`, issues);
    if (!Array.isArray(zone.channelIds)) {
      issue(issues, `${path}.channelIds`, 'array', 'Tableau de références attendu.');
      return;
    }
    const seen = new Set<string>();
    Array.from(zone.channelIds).forEach((id: unknown, referenceIndex: number) => {
      const referencePath = `${path}.channelIds[${referenceIndex}]`;
      identifier(id, referencePath, seen, issues);
      if (typeof id === 'string' && !channelIds.has(id)) {
        issue(issues, referencePath, 'missing_channel', 'Canal référencé absent.');
      }
    });
    if (scan && zone.priorityChannelId !== null && (typeof zone.priorityChannelId !== 'string' || !zone.channelIds.includes(zone.priorityChannelId))) {
      issue(issues, `${path}.priorityChannelId`, 'priority_member', 'Le canal prioritaire doit appartenir à la liste, ou être null.');
    }
  });
}

/** Validate untrusted parsed JSON without changing or dropping any fields. */
export function validateCodeplug(value: unknown): ValidationIssue[] {
  return validateDocument(value, 2);
}

export function validateLegacyCodeplug(value: unknown): ValidationIssue[] {
  return validateDocument(value, 1);
}

function validateDocument(value: unknown, version: 1 | 2): ValidationIssue[] {
  const issues: Issues = [];
  if (!record(value, '$', ['format', 'schemaVersion', 'name', 'channels', 'zones', 'vfo', ...(version === 2 ? ['scanLists'] : [])], issues)) return issues;
  if (value.format !== 'opend578-codeplug') issue(issues, '$.format', 'format', 'Format OpenD578 attendu.');
  if (value.schemaVersion !== version) issue(issues, '$.schemaVersion', 'version', 'Version non prise en charge ; conversion v1 explicite requise le cas échéant.');
  text(value.name, '$.name', issues);
  const channelIds = channels(value.channels, issues);
  zones(value.zones, channelIds, issues);
  if (version === 2) zones(value.scanLists, channelIds, issues, true);
  if (value.vfo !== null && record(value.vfo, '$.vfo', SETTINGS_KEYS, issues)) settings(value.vfo, '$.vfo', issues);
  return issues;
}

export class CodeplugValidationError extends Error {
  readonly issues: ValidationIssue[];

  constructor(issues: ValidationIssue[]) {
    super(issues.map(({ path, message }) => `${path} : ${message}`).join('\n'));
    this.name = 'CodeplugValidationError';
    this.issues = issues;
  }
}

export function assertCodeplug(value: unknown): asserts value is Codeplug {
  const issues = validateCodeplug(value);
  if (issues.length) throw new CodeplugValidationError(issues);
}
