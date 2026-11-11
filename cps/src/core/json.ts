import type { Codeplug } from './model.ts';
import { assertCodeplug, CodeplugValidationError } from './validation.ts';

/** Fails closed on malformed, future-version or unknown-field files. */
export function parseCodeplug(source: string): Codeplug {
  let value: unknown;
  try {
    value = JSON.parse(source);
  } catch {
    throw new CodeplugValidationError([{ path: '$', code: 'json', message: 'JSON invalide.' }]);
  }
  assertCodeplug(value);
  return value;
}

/** JSON serialization also validates callers that bypass TypeScript types. */
export function serializeCodeplug(value: Codeplug): string {
  assertCodeplug(value);
  return `${JSON.stringify(value, null, 2)}\n`;
}
