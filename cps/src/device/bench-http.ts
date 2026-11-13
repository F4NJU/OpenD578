import { assertOemReadOnly } from './oem-readonly.ts';
import { assertOpenD578ReadOnly } from './opend578-readonly.ts';
import type { BenchReply } from './oem-readonly.ts';

export function benchOrigin(value: string): string {
  const url = new URL(value);
  if (url.protocol !== 'http:' || !['localhost', '127.0.0.1', '[::1]'].includes(url.hostname) || url.username || url.password || url.search || url.hash || !['', '/'].includes(url.pathname)) {
    throw new Error('Indiquez uniquement l’adresse HTTP locale du banc, par exemple http://127.0.0.1:8000.');
  }
  return url.origin;
}

/** Same-origin only: retains the bench token and origin checks without adding CORS. */
export class BenchHttpApi {
  private token = '';
  private signal: AbortSignal;
  private fetcher: typeof fetch;
  private validateWrite: (bytes: Uint8Array) => void;
  constructor(options: { signal?: AbortSignal; fetcher?: typeof fetch; protocol?: 'oem' | 'opend578-ro' } = {}) {
    this.signal = options.signal ?? new AbortController().signal;
    // Browser fetch requires its Window/Worker receiver. Calling an unbound
    // function as this.fetcher(...) supplies the adapter as receiver instead.
    this.fetcher = options.fetcher ?? globalThis.fetch.bind(globalThis);
    this.validateWrite = options.protocol === 'opend578-ro' ? assertOpenD578ReadOnly : assertOemReadOnly;
  }
  async initialize(): Promise<void> {
    const config = await this.request('config');
    if (typeof config.token !== 'string' || !config.token || !config.capabilities || typeof config.capabilities !== 'object' || (config.capabilities as BenchReply).usb_cdc !== true) {
      throw new Error('Ce serveur ne fournit pas l’API USB du banc OpenD578.');
    }
    this.token = config.token;
  }
  async request(path: string, data?: Record<string, unknown>): Promise<BenchReply> {
    this.signal.throwIfAborted();
    const getAllowed = path === 'config' || path === 'usb/cdc?view=summary' || /^usb\/cdc\?cursor=\d+$/.test(path);
    const postAllowed = path === 'usb/start' || path === 'usb/write';
    if (data === undefined ? !getAllowed : !postAllowed) throw new Error('Route interdite par le client de lecture.');
    if (data !== undefined && !this.token) throw new Error('Banc non identifié.');
    if (path === 'usb/write') {
      if (typeof data?.hex !== 'string' || !/^(?:[a-f0-9]{2})+$/i.test(data.hex)) throw new Error('Commande hexadécimale invalide.');
      this.validateWrite(Uint8Array.from(data.hex.match(/../g)!, byte => parseInt(byte, 16)));
    }
    let response: Response;
    try {
      response = await this.fetcher('/api/' + path, { method: data === undefined ? 'GET' : 'POST',
        headers: data === undefined ? {} : { 'Content-Type': 'application/json', 'X-Lab-Token': this.token },
        body: data === undefined ? undefined : JSON.stringify(data),
        signal: AbortSignal.any([this.signal, AbortSignal.timeout(5000)]), credentials: 'same-origin', cache: 'no-store', redirect: 'error' });
    } catch { this.signal.throwIfAborted(); throw new Error('API du banc inaccessible ou trop lente. Vérifiez que le CPS est ouvert depuis /cps/ sur le banc Python.'); }
    const value: unknown = await response.json();
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Réponse du banc invalide.');
    if (!response.ok) throw new Error(typeof (value as BenchReply).error === 'string' ? String((value as BenchReply).error) : `Erreur HTTP ${response.status}`);
    return value as BenchReply;
  }
}
