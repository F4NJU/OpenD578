import type { Codeplug, Channel } from './model.ts';
import type { OemSnapshot, OemSlot } from '../device/oem-readonly.ts';
import { assertCodeplug } from './validation.ts';

export function oemImportReason(slot: OemSlot): string | null {
  if (slot.mode !== 'FM') return 'Mode FM seul requis';
  if (typeof slot.name !== 'string' || !/^[\x20-\x7e]{1,16}$/.test(slot.name) || !slot.name.trim()) return 'Nom absent ou non interprétable';
  if (!Number.isSafeInteger(slot.rxHz) || slot.rxHz! <= 0 || !Number.isSafeInteger(slot.txHz) || slot.txHz! <= 0) return 'Fréquence RX/TX inconnue ou invalide';
  for (const tone of [slot.rxTone, slot.txTone]) {
    if (!tone || tone.kind === 'unknown') return 'Tonalité RX/TX inconnue';
    if (tone.kind === 'dcs') return 'DCS non pris en charge dans le document FM';
    if (tone.kind === 'ctcss' && (!Number.isSafeInteger(tone.deciHz) || tone.deciHz < 600 || tone.deciHz > 2600)) return 'CTCSS invalide';
  }
  return null;
}

export function mergeOemSnapshots(previous: OemSnapshot | null, next: OemSnapshot): OemSnapshot {
  if (!previous || previous.engine !== next.engine || previous.endAcknowledged || next.scope === 'active-channels') return structuredClone(next);
  const slots = new Map(previous.slots.map(slot => [slot.slot, slot]));
  for (const slot of next.slots) slots.set(slot.slot, slot);
  return { ...next, page: -1, scope: 'collected-pages', slots: [...slots.values()].sort((a,b) => a.slot-b.slot) };
}

/** PC preparation only: missing OEM settings are explicit choices, never decoded. */
export function appendOemSlots(value: Codeplug, snapshot: OemSnapshot, selected: number[],
  settings: { bandwidth: 'narrow' | 'wide'; power: string }, newId: () => string = () => crypto.randomUUID()): Codeplug {
  const collection = snapshot.page === -1 && ['active-channels', 'collected-pages'].includes(snapshot.scope ?? '');
  const validSlots = collection ? snapshot.slots.length <= 4000 && new Set(snapshot.slots.map(slot => slot.slot)).size === snapshot.slots.length && snapshot.slots.every(slot => Number.isInteger(slot.slot) && slot.slot >= 1 && slot.slot <= 4000) : Number.isInteger(snapshot.page) && snapshot.page >= 0 && snapshot.page <= 3 && snapshot.slots.length === 32 && snapshot.slots.every((slot, index) => slot.slot === snapshot.page * 32 + index + 1);
  if (snapshot.model !== 'D578UV' || snapshot.endAcknowledged !== true || !validSlots) throw new Error('Instantané OEM incomplet ou invalide.');
  if (!selected.length || new Set(selected).size !== selected.length) throw new Error('Sélection vide ou répétée.');
  if (!['narrow', 'wide'].includes(settings.bandwidth) || typeof settings.power !== 'string' || !settings.power.trim()) throw new Error('Choisir la largeur et la puissance de préparation.');
  const channels: Channel[] = selected.map(number => {
    const slot = snapshot.slots.find(item => item.slot === number);
    if (!slot) throw new Error('Emplacement absent de cet instantané.');
    const reason = oemImportReason(slot);
    if (reason) throw new Error(`Emplacement ${number} : ${reason}.`);
    return { id: newId(), name: slot.name!, mode: 'FM', rxHz: slot.rxHz!, txHz: slot.txHz!,
      bandwidth: settings.bandwidth, power: settings.power,
      rxCtcssDeciHz: slot.rxTone.kind === 'ctcss' ? slot.rxTone.deciHz : null, txCtcssDeciHz: slot.txTone.kind === 'ctcss' ? slot.txTone.deciHz : null, txInhibit: true };
  });
  const next = { ...value, channels: [...value.channels, ...channels] };
  assertCodeplug(next);
  return next;
}
