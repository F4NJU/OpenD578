import type { BenchApi, BenchReply } from './oem-readonly.ts';
export interface OpenD578Vfo { id: 'A' | 'B'; rxHz: number; bandwidth: 'narrow' | 'wide'; txInhibit: true; }
export interface OpenD578LiveSnapshot {
  format: 'opend578-live-vfos-v1'; firmware: string; engine: string; readAt: string;
  capabilities: Record<string, boolean>; selected: 'A' | 'B'; vfos: OpenD578Vfo[];
}
export function assertOpenD578ReadOnly(bytes: Uint8Array): void {
  const value = new TextDecoder().decode(bytes);
  const match = /^OD578\/1 ([1-9][0-9]{0,4}) (HELLO|VFOS)\n$/.exec(value);
  if (!match || Number(match[1]) > 65535) throw new Error('Commande OpenD578 interdite : identification et VFO en lecture seule.');
}
interface NativeCdc extends BenchReply {
  state: string; session: string; engine_instance: string; sent_total: number; queued_bytes: number;
  received_total: number; received_base: number; received_hex: string;
}
function nativeState(value: BenchReply): NativeCdc {
  if (typeof value.state !== 'string' || typeof value.engine_instance !== 'string') throw new Error('État USB invalide.');
  if (value.state === 'ready' && (typeof value.session !== 'string' || !value.session ||
    ['sent_total','queued_bytes','received_total'].some(key => !Number.isSafeInteger(value[key]) || Number(value[key]) < 0))) throw new Error('Session ou compteurs USB invalides.');
  return value as NativeCdc;
}
export class OpenD578ReadOnlyClient {
  private api: BenchApi; private signal: AbortSignal; private busy = false;
  private engine = ''; private session = ''; private cursor = 0; private sent = 0; private id = 0;
  constructor(api: BenchApi, options: { signal?: AbortSignal } = {}) { this.api = api; this.signal = options.signal ?? new AbortController().signal; }
  private async pause(): Promise<void> { this.signal.throwIfAborted(); await new Promise(resolve => setTimeout(resolve, 20)); this.signal.throwIfAborted(); }
  private async connect(): Promise<void> {
    let state = nativeState(await this.api('usb/cdc?view=summary'));
    if (state.state === 'disconnected') await this.api('usb/start', {});
    const deadline = Date.now() + 40000;
    do {
      this.signal.throwIfAborted(); state = nativeState(await this.api('usb/cdc?view=summary'));
      if (state.state === 'ready' && !state.retryable) break;
      if (['error','stopped'].includes(state.state) || Date.now() > deadline) throw new Error('Le firmware OpenD578 et son USB doivent être démarrés dans le banc matériel.');
      await this.pause();
    } while (true);
    if (state.queued_bytes) throw new Error('Un autre client USB est actif.');
    this.engine = state.engine_instance; this.session = state.session; this.cursor = state.received_total; this.sent = state.sent_total;
  }
  private async command(command: 'HELLO' | 'VFOS'): Promise<BenchReply> {
    const id = ++this.id; if (id > 65535) throw new Error('Créer un nouveau client de lecture.');
    const bytes = new TextEncoder().encode(`OD578/1 ${id} ${command}\n`); assertOpenD578ReadOnly(bytes);
    this.signal.throwIfAborted(); await this.api('usb/write', { session: this.session, hex: Array.from(bytes, byte => byte.toString(16).padStart(2,'0')).join('') }); this.sent += bytes.length;
    const output: number[] = [], deadline = Date.now() + 20000;
    while (Date.now() < deadline) {
      this.signal.throwIfAborted(); const state = nativeState(await this.api(`usb/cdc?cursor=${this.cursor}`));
      if (state.retryable) { await this.pause(); continue; }
      if (state.state !== 'ready' || state.session !== this.session || state.engine_instance !== this.engine ||
        !Number.isSafeInteger(state.received_base) || state.received_base < 0 || state.received_base > this.cursor || state.received_total < this.cursor ||
        state.sent_total > this.sent || typeof state.received_hex !== 'string' || !/^(?:[0-9a-f]{2})*$/i.test(state.received_hex)) throw new Error('Session modifiée ou trafic USB inattendu.');
      const incoming = Uint8Array.from(state.received_hex.match(/../g) ?? [], byte => parseInt(byte,16));
      if (incoming.length !== state.received_total - state.received_base) throw new Error('Tampon USB incohérent.');
      output.push(...incoming.slice(this.cursor - state.received_base)); this.cursor = state.received_total;
      const end = output.indexOf(10);
      if (output.length > 384 || end >= 0 && end !== output.length - 1) throw new Error('Réponse supplémentaire ou trop longue.');
      if (end >= 0 && state.sent_total === this.sent && !state.queued_bytes) {
        const reply: unknown = JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(Uint8Array.from(output)));
        if (!reply || typeof reply !== 'object' || Array.isArray(reply)) throw new Error('Réponse OpenD578 invalide.');
        const result = reply as BenchReply;
        if (result.protocol !== 'opend578-cps' || result.version !== 1 || result.id !== id) throw new Error('Protocole ou identifiant de réponse incorrect.');
        if (typeof result.error === 'string') throw new Error(`Firmware : ${result.error}`);
        return result;
      }
      await this.pause();
    }
    throw new Error('Délai OpenD578 dépassé. Aucune commande n’est répétée automatiquement.');
  }
  async readVfos(): Promise<OpenD578LiveSnapshot> {
    if (this.busy) throw new Error('Lecture déjà en cours.'); this.busy = true;
    try {
      await this.connect(); const hello = await this.command('HELLO');
      const keys = ['vfoRead','vfoWrite','memories','ctcss','dcs','tx','persistent'];
      const capabilities = hello.capabilities as Record<string, boolean>;
      if (typeof hello.firmware !== 'string' || !/^[\x20-\x7e]{1,64}$/.test(hello.firmware) || !capabilities ||
        typeof capabilities !== 'object' || Array.isArray(capabilities) || Object.keys(capabilities).length !== keys.length ||
        keys.some(key => typeof capabilities[key] !== 'boolean') || !capabilities.vfoRead) throw new Error('Identité ou capacités OpenD578 invalides.');
      const reply = await this.command('VFOS');
      if (!['A','B'].includes(String(reply.selected)) || !Array.isArray(reply.vfos) || reply.vfos.length !== 2) throw new Error('Deux VFO A/B attendus.');
      reply.vfos.forEach((vfo, index) => {
        if (!vfo || typeof vfo !== 'object' || vfo.id !== ['A','B'][index] || Object.keys(vfo).length !== 4 || !Number.isSafeInteger(vfo.rxHz) || vfo.rxHz <= 0 ||
          !['narrow','wide'].includes(vfo.bandwidth) || vfo.txInhibit !== true) throw new Error('Valeur VFO invalide ou émission non inhibée.');
      });
      return { format:'opend578-live-vfos-v1', firmware:hello.firmware, engine:this.engine, readAt:new Date().toISOString(), capabilities,
        selected:reply.selected as 'A' | 'B', vfos:reply.vfos as OpenD578Vfo[] };
    } finally { this.busy = false; }
  }
}
