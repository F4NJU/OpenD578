import type { Codeplug } from './model.ts';
import { assertCodeplug, CodeplugValidationError, validateLegacyCodeplug } from './validation.ts';

/** Fails closed on malformed, future-version or unknown-field files. */
export function parseCodeplug(source: string, options: { upgradeV1?: boolean } = {}): Codeplug {
  let value: unknown;
  try {
    value = JSON.parse(source);
  } catch {
    throw new CodeplugValidationError([{ path: '$', code: 'json', message: 'JSON invalide.' }]);
  }
  if (options.upgradeV1 && value !== null && typeof value === 'object' && (value as Record<string, unknown>).schemaVersion === 1) {
    const issues = validateLegacyCodeplug(value);
    if (issues.length) throw new CodeplugValidationError(issues);
    value = { ...(value as Record<string, unknown>), schemaVersion: 2, scanLists: [] };
  }
  assertCodeplug(value);
  return value;
}

/** JSON serialization also validates callers that bypass TypeScript types. */
export function serializeCodeplug(value: Codeplug): string {
  assertCodeplug(value);
  return `${JSON.stringify(value, null, 2)}\n`;
}
