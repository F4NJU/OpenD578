import { OEM_CAPACITY, OEM_BITMAP, OEM_BITMAP_BYTES, oemChannelAddress, oemReadableAddress, oemActiveSlots, decodeOemTone } from './oem-profile.ts';
import type { OemTone } from './oem-profile.ts';
/** OEM V1.21 research profile: host-side transactions, never NAND/MCU access. */
export const OEM_BASE = 0x00800000;
const PAGE_BYTES = 2048;
const MODELS = ['FM', 'DMR', 'FM + DMR RX', 'DMR + FM RX'];
const POWER_NAMES = ['Low', 'Mid', 'High', 'Turbo'];
export type BenchReply = Record<string, unknown>;
export type BenchApi = (path: string, data?: Record<string, unknown>) => Promise<BenchReply>;
export interface OemSlot {
  slot: number;
  name: string | null;
  rxHz: number | null;
  txHz: number | null;
  mode: string;
  power: string;
  rxTone: OemTone;
  txTone: OemTone;
}
export interface OemSnapshot {
  engine: string;
  model: 'D578UV';
  page: number;
  scope?: 'active-channels' | 'collected-pages';
  readAt: string;
  slots: OemSlot[];
  endAcknowledged: boolean;
}
interface CdcState {
  state: string; engine_instance: string; session: string;
  received_total: number; received_base: number; sent_total: number;
  queued_bytes: number; received_hex: string; error?: string; retryable?: boolean;
}

function oemHex(bytes: Uint8Array): string { return Array.from(bytes, value => value.toString(16).padStart(2, '0')).join(''); }
function oemUnhex(value: unknown): Uint8Array {
  if (typeof value !== 'string' || !/^(?:[a-f0-9]{2})*$/i.test(value)) throw new Error('Flux USB hexadécimal invalide.');
  return Uint8Array.from(value.match(/../g) ?? [], byte => parseInt(byte, 16));
}
function integer(value: unknown): value is number { return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0; }
function checkCdc(value: BenchReply, withBytes: boolean): CdcState {
  if (typeof value.state !== 'string' || typeof value.engine_instance !== 'string') throw new Error('État du banc invalide.');
  if (value.state === 'ready') {
    if (typeof value.session !== 'string' || !value.session ||
      !integer(value.received_total) || !integer(value.sent_total) || !integer(value.queued_bytes)) throw new Error('Compteurs/session USB invalides.');
    if (withBytes && (!integer(value.received_base) || value.received_base > value.received_total)) throw new Error('Tampon USB invalide.');
  }
  return value as unknown as CdcState;
}

export function oemReadCommand(address: number): Uint8Array {
  if (!oemReadableAddress(address)) throw new Error('Lecture hors des canaux et du bitmap OEM autorisés.');
  return new Uint8Array([82, address >>> 24, (address >>> 16) & 255, (address >>> 8) & 255, address & 255, 16]);
}
/** Strict allowlist also applied at the HTTP transport boundary. No W command. */
export function assertOemReadOnly(bytes: Uint8Array): void {
  const text = new TextDecoder().decode(bytes);
  if (text === 'PROGRAM' || text === 'END' || (bytes.length === 1 && bytes[0] === 2)) return;
  if (bytes.length === 6 && bytes[0] === 82 && bytes[5] === 16) {
    const address = bytes[1] * 0x1000000 + (bytes[2] << 16) + (bytes[3] << 8) + bytes[4];
    oemReadCommand(address); return;
  }
  throw new Error('Commande interdite : cet adaptateur est strictement en lecture seule.');
}
function checkOemResponse(response: Uint8Array, address: number): Uint8Array {
  const command = oemReadCommand(address);
  if (response.length !== 24 || response[0] !== 87 || response[5] !== 16 || response[23] !== 6 ||
    !response.slice(1, 5).every((value, index) => value === command[index + 1]) ||
    response.slice(1, 22).reduce((sum, value) => sum + value, 0) % 256 !== response[22]) throw new Error('Réponse OEM invalide (adresse, taille, checksum ou ACK).');
  return response.slice(6, 22);
}
function oemBcd(bytes: Uint8Array): number | null {
  let result = 0;
  for (const byte of bytes) { if ((byte >> 4) > 9 || (byte & 15) > 9) return null; result = result * 100 + (byte >> 4) * 10 + (byte & 15); }
  return result > 0 ? result * 10 : null;
}
export function decodeOemPage(bytes: Uint8Array, page: number): OemSlot[] {
  if (bytes.length !== PAGE_BYTES || !Number.isInteger(page) || page < 0 || page > 3) throw new Error('Page OEM invalide.');
  return Array.from({ length: 32 }, (_, index) => decodeOemRecord(bytes.slice(index * 64, (index + 1) * 64), page * 32 + index + 1));
}
export function decodeOemRecord(record: Uint8Array, slot: number): OemSlot {
  if (record.length !== 64 || !Number.isInteger(slot) || slot < 1 || slot > OEM_CAPACITY) throw new Error('Canal OEM invalide.');
  const nameBytes = record.slice(35, 51);
    const end = nameBytes.indexOf(0), rawName = end < 0 ? nameBytes : nameBytes.slice(0, end);
    const rx = oemBcd(record.slice(0, 4));
    // Offset zero is valid, whereas an all-zero RX does not identify a usable channel.
    const offset = record.slice(4, 8).every(byte => byte === 0) ? 0 : oemBcd(record.slice(4, 8));
    const shift = record[8] >> 6;
    const tx = rx === null || offset === null || shift === 3 ? null : rx + (shift === 0 ? 0 : shift === 1 ? offset : -offset);
    return { slot,
      name: rawName.length && rawName.every(byte => byte >= 32 && byte <= 126) ? String.fromCharCode(...rawName) : null,
      rxHz: rx, txHz: tx !== null && tx > 0 ? tx : null,
      mode: MODELS[record[8] & 3], power: POWER_NAMES[(record[8] >> 2) & 3], rxTone: decodeOemTone(record, 'rx'), txTone: decodeOemTone(record, 'tx') };
}

/** Read sessions may span pages; END or ambiguous failures require a fresh engine. */
export class OemReadOnlyClient {
  private api: BenchApi;
  private signal: AbortSignal;
  private progress: (done: number, total: number) => void;
  private markEngine: (engine: string | null) => void;
  private spent: string | null;
  private programming = false;
  private faulted = false;
  get sessionOpen(): boolean { return this.programming && !this.faulted; }
  private engine = ''; private session = ''; private cursor = 0; private sent = 0; private busy = false;

  constructor(api: BenchApi, options: { signal?: AbortSignal; progress?: (done: number, total: number) => void; spentEngine?: string | null; markEngine?: (engine: string | null) => void } = {}) {
    this.api = api; this.signal = options.signal ?? new AbortController().signal;
    this.progress = options.progress ?? (() => {}); this.spent = options.spentEngine ?? null;
    this.markEngine = options.markEngine ?? (() => {});
  }
  private checkAbort(): void { this.signal.throwIfAborted(); }
  private async pause(): Promise<void> {
    this.checkAbort();
    await new Promise<void>((resolve, reject) => {
      const abort = (): void => { clearTimeout(timer); reject(this.signal.reason); };
      const timer = setTimeout(() => { this.signal.removeEventListener('abort', abort); resolve(); }, 15);
      this.signal.addEventListener('abort', abort, { once: true });
    });
  }
  private async status(path = 'usb/cdc?view=summary', bytes = false): Promise<CdcState> {
    this.checkAbort();
    return checkCdc(await this.api(path), bytes);
  }
  private async connect(): Promise<void> {
    let state = await this.status();
    if (state.engine_instance === this.spent) throw new Error('Redémarrez le moteur du banc avant une nouvelle lecture (session OEM déjà utilisée).');
    if (state.state === 'disconnected') { await this.api('usb/start', {}); }
    const deadline = Date.now() + 40000;
    while (true) {
      this.checkAbort(); state = await this.status();
      if (state.engine_instance === this.spent) throw new Error('Moteur déjà utilisé : redémarrage requis.');
      if (state.state === 'ready' && !state.retryable) break;
      if (['stopped', 'error'].includes(state.state) || Date.now() > deadline) throw new Error(state.error || 'Le moteur OEM doit être démarré et son USB prêt.');
      await this.pause();
    }
    if (state.queued_bytes !== 0) throw new Error('Un client USB est déjà actif : fermez le CPS intégré et les ponts externes.');
    this.engine = state.engine_instance; this.session = state.session; this.cursor = state.received_total; this.sent = state.sent_total;
  }
  private async exchange(request: Uint8Array, expected: number): Promise<Uint8Array> {
    this.checkAbort(); assertOemReadOnly(request);
    await this.api('usb/write', { session: this.session, hex: oemHex(request) });
    this.sent += request.length;
    const output: number[] = [], deadline = Date.now() + 20000;
    while (Date.now() < deadline) {
      this.checkAbort();
      const state = await this.status(`usb/cdc?cursor=${this.cursor}`, true);
      if (state.retryable) { await this.pause(); continue; }
      if (state.state !== 'ready' || state.session !== this.session || state.engine_instance !== this.engine) throw new Error('Session ou moteur USB modifié pendant la lecture.');
      if (state.received_base > this.cursor || state.received_total < this.cursor) throw new Error('Débordement ou réinitialisation du tampon USB.');
      const bytes = oemUnhex(state.received_hex);
      if (bytes.length !== state.received_total - state.received_base) throw new Error('Longueur du tampon USB incohérente.');
      output.push(...bytes.slice(this.cursor - state.received_base)); this.cursor = state.received_total;
      if (output.length > expected || state.sent_total > this.sent) throw new Error('Octets inattendus : un autre client USB peut être actif.');
      if (output.length === expected && state.sent_total === this.sent && state.queued_bytes === 0) return Uint8Array.from(output);
      await this.pause();
    }
    throw new Error('Délai de réponse OEM dépassé. Aucune commande n’est répétée ; redémarrez le banc.');
  }
  private async finishSession(): Promise<void> {
    await this.checkOwnedSession();
    if (oemHex(await this.exchange(new TextEncoder().encode('END'), 1)) !== '06') throw new Error('END non acquitté ; redémarrez le banc.');
    this.programming = false;
  }
  private async checkOwnedSession(): Promise<void> {
    const state = await this.status();
    if (state.state !== 'ready' || state.retryable || state.engine_instance !== this.engine || state.session !== this.session ||
      state.sent_total !== this.sent || state.received_total !== this.cursor || state.queued_bytes !== 0) throw new Error('Session USB modifiée : redémarrez le banc.');
  }
  async endSession(): Promise<void> {
    if (this.busy) throw new Error('Une lecture est déjà en cours.');
    if (this.faulted) throw new Error('Session interrompue : redémarrez le banc.');
    if (!this.programming) return;
    this.busy = true;
    try { await this.finishSession(); }
    catch (error) { this.faulted = true; this.programming = false; throw error; }
    finally { this.busy = false; }
  }
  private async beginSession(): Promise<void> {
    if (this.faulted) throw new Error('Session interrompue : redémarrez le banc.');
      if (!this.programming) {
        await this.connect(); this.checkAbort();
        this.spent = this.engine; this.markEngine(this.engine);
        const response = await this.exchange(new TextEncoder().encode('PROGRAM'), 3);
        if (oemHex(response) !== '515806') throw new Error('Réponse PROGRAM non reconnue.');
        const identity = await this.exchange(new Uint8Array([2]), 16);
        if (oemHex(identity.slice(0, 8)) !== '4944353738555600' || identity[15] !== 6) throw new Error('Identité OEM D578UV non reconnue : lecture refusée.');
        this.programming = true;
      } else {
        await this.checkOwnedSession();
      }
  }
  async readAll(options: { keepSession?: boolean } = {}): Promise<OemSnapshot> {
    if (this.busy) throw new Error('Une lecture est déjà en cours.');
    this.busy = true;
    try {
      await this.beginSession();
      const bitmap = new Uint8Array(OEM_BITMAP_BYTES);
      for (let offset = 0; offset < bitmap.length; offset += 16) {
        const address = OEM_BITMAP + offset;
        bitmap.set(checkOemResponse(await this.exchange(oemReadCommand(address), 24), address), offset);
        this.progress(offset + 16, OEM_BITMAP_BYTES + OEM_CAPACITY * 64);
      }
      const active = oemActiveSlots(bitmap), slots: OemSlot[] = [];
      const total = OEM_BITMAP_BYTES + active.length * 64;
      this.progress(OEM_BITMAP_BYTES, total);
      for (const slot of active) {
        const record = new Uint8Array(64), base = oemChannelAddress(slot);
        for (let offset = 0; offset < 64; offset += 16) {
          const address = base + offset;
          record.set(checkOemResponse(await this.exchange(oemReadCommand(address), 24), address), offset);
        }
        slots.push(decodeOemRecord(record, slot));
        this.progress(OEM_BITMAP_BYTES + slots.length * 64, total);
      }
      if (!options.keepSession) await this.finishSession();
      return { engine: this.engine, model: 'D578UV', page: -1, scope: 'active-channels', readAt: new Date().toISOString(), slots, endAcknowledged: !options.keepSession };
    } catch (error) { this.faulted = true; this.programming = false; throw error; }
    finally { this.busy = false; }
  }
  async readPage(page: number, options: { keepSession?: boolean } = {}): Promise<OemSnapshot> {
    if (this.busy) throw new Error('Une lecture est déjà en cours.');
    if (!Number.isInteger(page) || page < 0 || page > 3) throw new Error('Choisir un groupe de 32 emplacements entre 1 et 128.');
    this.busy = true;
    try {
      if (this.faulted) throw new Error('Session interrompue : redémarrez le banc.');
      await this.beginSession();
      const bytes = new Uint8Array(PAGE_BYTES);
      for (let offset = 0; offset < PAGE_BYTES; offset += 16) {
        const address = OEM_BASE + page * PAGE_BYTES + offset;
        bytes.set(checkOemResponse(await this.exchange(oemReadCommand(address), 24), address), offset);
        this.progress(offset + 16, PAGE_BYTES);
      }
      if (!options.keepSession) await this.finishSession();
      return { engine: this.engine, model: 'D578UV', page, readAt: new Date().toISOString(), slots: decodeOemPage(bytes, page), endAcknowledged: !options.keepSession };
    } catch (error) { this.faulted = true; this.programming = false; throw error; } finally { this.busy = false; }
  }
}
