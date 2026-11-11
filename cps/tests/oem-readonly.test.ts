import test from 'node:test';
import assert from 'node:assert/strict';
import { OemReadOnlyClient, OEM_BASE, assertOemReadOnly, decodeOemPage, oemReadCommand } from '../src/device/oem-readonly.ts';
import type { BenchReply } from '../src/device/oem-readonly.ts';
import { BenchHttpApi, benchOrigin } from '../src/device/bench-http.ts';

const toHex = (bytes: Uint8Array): string => Buffer.from(bytes).toString('hex');
function samplePage(): Uint8Array {
  const page = new Uint8Array(2048).fill(255);
  page.fill(0, 0, 64);
  page.set([0x14, 0x55, 0, 0, 0, 0x06, 0, 0, 0x40]);
  page.set(new TextEncoder().encode('TEST'), 35);
  return page;
}

// Host protocol fixtures only: these canned replies do not qualify a firmware or emulator.
function wire(options: { corrupt?: boolean; wrongId?: boolean; extra?: boolean; reset?: boolean; overflow?: boolean; split?: boolean } = {}) {
  const requests: Uint8Array[] = [];
  const source = samplePage();
  let sent = 0, total = 0, engine = 'engine-a', polls = 0;
  let pending = new Uint8Array();
  const state = (): BenchReply => ({ state: 'ready', engine_instance: engine, session: 'session-a',
    sent_total: sent, queued_bytes: 0, received_total: total, received_base: total, received_hex: '' });
  const api = async (path: string, data?: Record<string, unknown>): Promise<BenchReply> => {
    if (path === 'usb/cdc?view=summary') return state();
    if (path === 'usb/write') {
      const bytes = Uint8Array.from(Buffer.from(String(data!.hex), 'hex')); requests.push(bytes); sent += bytes.length;
      if (toHex(bytes) === '50524f4752414d') pending = new Uint8Array([81, 88, 6]);
      else if (bytes[0] === 2) { pending = new Uint8Array(16); pending.set([73, 68, 53, 55, 56, 85, 86, 0]); pending[15] = 6; if (options.wrongId) pending[1] = 0; }
      else if (bytes[0] === 82) {
        const address = bytes[1] * 0x1000000 + (bytes[2] << 16) + (bytes[3] << 8) + bytes[4];
        pending = new Uint8Array(24); pending.set(bytes); pending[0] = 87;
        pending.set(source.slice((address - OEM_BASE) % 2048, (address - OEM_BASE) % 2048 + 16), 6);
        pending[22] = pending.slice(1, 22).reduce((sum, byte) => sum + byte, 0) & 255; pending[23] = 6;
        if (options.corrupt) pending[22] ^= 1;
      } else pending = new Uint8Array([6]);
      if (options.extra && requests.length === 1) pending = new Uint8Array([...pending, 42]);
      return { queued: true };
    }
    assert.match(path, /^usb\/cdc\?cursor=\d+$/);
    polls++;
    const cursor = Number(path.split('=')[1]);
    const received = options.split ? pending.slice(0, 2) : pending;
    pending = pending.slice(received.length); total += received.length;
    if (options.reset && polls === 2) engine = 'engine-b';
    return { ...state(), received_base: options.overflow ? cursor + 1 : cursor, received_total: total,
      received_hex: toHex(received) };
  };
  return { api, requests, source };
}

test('bounded transaction identifies and reads exactly 32 slots then sends END, with no W frames', async () => {
  const fixture = wire(); let marked = ''; let done = 0;
  const client = new OemReadOnlyClient(fixture.api, { markEngine: engine => { marked = engine; }, progress: count => { done = count; } });
  const result = await client.readPage(3);
  assert.equal(result.model, 'D578UV'); assert.equal(result.slots[0].slot, 97);
  assert.equal(result.slots[0].name, 'TEST'); assert.equal(result.slots[0].txHz, 146100000);
  assert.equal(result.slots[1].name, null); assert.equal(result.slots[1].rxHz, null);
  assert.equal(marked, 'engine-a'); assert.equal(done, 2048);
  assert.equal(fixture.requests.length, 131);
  assert.equal(fixture.requests.filter(bytes => bytes[0] === 82).length, 128);
  assert.equal(toHex(fixture.requests.at(-1)!), '454e44');
  assert(fixture.requests.every(bytes => bytes[0] !== 87));
  fixture.requests.forEach(assertOemReadOnly);
  const before = fixture.requests.length;
  await assert.rejects(client.readPage(0), /Redémarrez/);
  assert.equal(fixture.requests.length, before);
});

test('fragmented USB replies are reassembled without assuming one HTTP poll per response', async () => {
  const fixture = wire({ split: true });
  const result = await new OemReadOnlyClient(fixture.api).readPage(0);
  assert.equal(result.slots[0].rxHz, 145500000);
});

test('bad checksum, unrecognized identity, extra bytes, engine reset and overflow stop the transaction', async () => {
  for (const option of ['corrupt', 'wrongId', 'extra', 'reset', 'overflow'] as const) {
    const fixture = wire({ [option]: true });
    await assert.rejects(new OemReadOnlyClient(fixture.api).readPage(0));
    assert(fixture.requests.every(bytes => toHex(bytes) !== '454e44'), option);
    assert(fixture.requests.every(bytes => bytes[0] !== 87), option);
  }
});

test('aborted and invalid page requests send no command; cancellation after a block sends no next command', async () => {
  const fixture = wire(), controller = new AbortController(); controller.abort(new Error('Annulé'));
  await assert.rejects(new OemReadOnlyClient(fixture.api, { signal: controller.signal }).readPage(0), /Annulé/);
  await assert.rejects(new OemReadOnlyClient(fixture.api).readPage(4));
  assert.equal(fixture.requests.length, 0);
  const running = new AbortController();
  await assert.rejects(new OemReadOnlyClient(fixture.api, { signal: running.signal,
    progress: () => running.abort(new Error('Arrêt utilisateur')) }).readPage(0), /Arrêt utilisateur/);
  assert.equal(fixture.requests.length, 3); // PROGRAM, identity, first read only
});

test('read-only allowlist refuses writes, unaligned reads and any access outside known slots', () => {
  for (const bytes of [new Uint8Array([87]), new Uint8Array([85]),
    new Uint8Array([82, 0, 0x80, 0, 1, 16]), new Uint8Array([82, 0, 0x80, 0x20, 0, 16])]) {
    assert.throws(() => assertOemReadOnly(bytes));
  }
  assert.throws(() => oemReadCommand(OEM_BASE - 16));
  assertOemReadOnly(oemReadCommand(OEM_BASE + 8192 - 16));
});

test('decoder keeps unknown names and frequency fields unknown, including unsupported shift', () => {
  const page = samplePage(); page[8] = 0xc0; page[35] = 0xff;
  const rows = decodeOemPage(page, 0);
  assert.equal(rows[0].txHz, null); assert.equal(rows[0].name, null);
  assert.equal(rows[1].rxHz, null);
  assert.throws(() => decodeOemPage(new Uint8Array(16), 0));
});

test('HTTP adapter preserves token checks and rejects mutating routes and W before fetch', async () => {
  const calls: { path: string; options?: RequestInit }[] = [];
  const fetcher = (async (path: string | URL | Request, options?: RequestInit) => {
    calls.push({ path: String(path), options });
    return new Response(JSON.stringify(String(path).endsWith('/config') ? { token: 'test-token', capabilities: { usb_cdc: true } } : { queued: true }));
  }) as typeof fetch;
  const api = new BenchHttpApi({ fetcher });
  await assert.rejects(api.request('usb/start', {}), /non identifié/);
  await api.initialize(); await api.request('usb/write', { session: 's', hex: '02' });
  assert.equal((calls[1].options!.headers as Record<string, string>)['X-Lab-Token'], 'test-token');
  assert.equal(calls[1].options!.credentials, 'same-origin');
  for (const [path, data] of [['start', {}], ['usb/stop', {}], ['usb/write', { hex: '57' }], ['../config', undefined]] as const) {
    await assert.rejects(api.request(path, data));
  }
  assert.equal(calls.length, 2);
});

test('bench address must be loopback HTTP without credentials, path, query or fragment', () => {
  assert.equal(benchOrigin('http://127.0.0.1:8765/'), 'http://127.0.0.1:8765');
  for (const url of ['https://127.0.0.1', 'http://example.org', 'http://u:p@localhost', 'http://localhost/api', 'http://localhost/?a=1', 'http://localhost/#x']) {
    assert.throws(() => benchOrigin(url), url);
  }
});
