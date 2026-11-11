import type { Channel, Codeplug } from './model.ts';
import { assertCodeplug } from './validation.ts';
import { serializeCodeplug } from './json.ts';

/** One validated transaction per user action. Callers never receive internal state. */
export class EditorHistory {
  private current: Codeplug;
  private past: Codeplug[] = [];
  private future: Codeplug[] = [];

  constructor(initial: Codeplug) { assertCodeplug(initial); this.current = structuredClone(initial); }
  get value(): Codeplug { return structuredClone(this.current); }
  get canUndo(): boolean { return this.past.length > 0; }
  get canRedo(): boolean { return this.future.length > 0; }

  commit(next: Codeplug): void {
    assertCodeplug(next);
    if (serializeCodeplug(next) === serializeCodeplug(this.current)) return;
    this.past = [...this.past.slice(-49), this.current];
    this.current = structuredClone(next); this.future = [];
  }
  undo(): void {
    if (!this.canUndo) return;
    this.future = [this.current, ...this.future];
    this.current = this.past.at(-1)!; this.past = this.past.slice(0, -1);
  }
  redo(): void {
    if (!this.canRedo) return;
    this.past = [...this.past, this.current];
    this.current = this.future[0]; this.future = this.future.slice(1);
  }
}

export function deleteChannels(value: Codeplug, ids: string[]): Codeplug {
  const removed = new Set(ids);
  return { ...value, channels: value.channels.filter(channel => !removed.has(channel.id)),
    zones: value.zones.map(zone => ({ ...zone, channelIds: zone.channelIds.filter(id => !removed.has(id)) })) };
}

/** CSV append is atomic and refuses collisions; JSON is the complete backup. */
export function appendChannels(value: Codeplug, channels: Channel[]): Codeplug {
  const next = { ...value, channels: [...value.channels, ...channels] };
  assertCodeplug(next);
  return next;
}

export function moveItem<T>(items: T[], index: number, delta: -1 | 1): T[] {
  const target = index + delta;
  if (index < 0 || index >= items.length || target < 0 || target >= items.length) return [...items];
  const next = [...items];
  [next[index], next[target]] = [next[target], next[index]];
  return next;
}
