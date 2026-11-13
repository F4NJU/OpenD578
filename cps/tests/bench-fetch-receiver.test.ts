import test from 'node:test';
import assert from 'node:assert/strict';
import { BenchHttpApi } from '../src/device/bench-http.ts';

test('default HTTP transport retains the browser global fetch receiver', async t => {
  const original = globalThis.fetch;
  const calls: string[] = [];
  globalThis.fetch = function(this: unknown, input: RequestInfo | URL): Promise<Response> {
    assert.equal(this, globalThis, 'Illegal invocation: fetch called with adapter receiver');
    calls.push(String(input));
    return Promise.resolve(Response.json({ token: 'test-token', capabilities: { usb_cdc: true } }));
  } as typeof fetch;
  t.after(() => { globalThis.fetch = original; });
  await new BenchHttpApi().initialize();
  assert.deepEqual(calls, ['/api/config']);
});
