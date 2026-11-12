import type { Codeplug, Channel } from './model.ts';
import type { OemSnapshot, OemSlot } from '../device/oem-readonly.ts';
import { assertCodeplug } from './validation.ts';

export function oemImportReason(slot: OemSlot): string | null {
  if (slot.mode !== 'FM') return 'Mode FM seul requis';
  if (typeof slot.name !== 'string' || !/^[\x20-\x7e]{1,16}$/.test(slot.name) || !slot.name.trim()) return 'Nom absent ou non interprétable';
  if (!Number.isSafeInteger(slot.rxHz) || slot.rxHz! <= 0 || !Number.isSafeInteger(slot.txHz) || slot.txHz! <= 0) return 'Fréquence RX/TX inconnue ou invalide';
  return null;
}

/** PC preparation only: missing OEM settings are explicit choices, never decoded. */
export function appendOemSlots(value: Codeplug, snapshot: OemSnapshot, selected: number[],
  settings: { bandwidth: 'narrow' | 'wide'; power: string }, newId: () => string = () => crypto.randomUUID()): Codeplug {
  if (snapshot.model !== 'D578UV' || snapshot.endAcknowledged !== true || !Number.isInteger(snapshot.page) || snapshot.page < 0 || snapshot.page > 3 || snapshot.slots.length !== 32 ||
    snapshot.slots.some((slot, index) => slot.slot !== snapshot.page * 32 + index + 1)) throw new Error('Instantané OEM incomplet ou invalide.');
  if (!selected.length || new Set(selected).size !== selected.length) throw new Error('Sélection vide ou répétée.');
  if (!['narrow', 'wide'].includes(settings.bandwidth) || typeof settings.power !== 'string' || !settings.power.trim()) throw new Error('Choisir la largeur et la puissance de préparation.');
  const channels: Channel[] = selected.map(number => {
    const slot = snapshot.slots.find(item => item.slot === number);
    if (!slot) throw new Error('Emplacement absent de cet instantané.');
    const reason = oemImportReason(slot);
    if (reason) throw new Error(`Emplacement ${number} : ${reason}.`);
    return { id: newId(), name: slot.name!, mode: 'FM', rxHz: slot.rxHz!, txHz: slot.txHz!,
      bandwidth: settings.bandwidth, power: settings.power,
      rxCtcssDeciHz: null, txCtcssDeciHz: null, txInhibit: true };
  });
  const next = { ...value, channels: [...value.channels, ...channels] };
  assertCodeplug(next);
  return next;
}
