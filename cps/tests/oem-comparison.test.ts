import test from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { compareOemPage, pageFromReplies } from '../../tools/compare_oem_page.mjs';
import { decodeOemPage } from '../src/device/oem-readonly.ts';

test('decoder matches the independent bench implementation across flags, offsets and names', () => {
  const page = new Uint8Array(2048);
  for (let i = 0; i < 32; i++) {
    page.set([0x14, 0x55, 0, 0, 0, 0x06, 0, 0, ((i % 4) << 6) | (i % 16)], i * 64);
    page.set(new TextEncoder().encode(`SYNTH${i}`), i * 64 + 35);
  }
  const reference = fileURLToPath(new URL('../../bench/web/mini_cps_protocol.js', import.meta.url));
  assert.equal(compareOemPage(page, decodeOemPage(page, 0), reference).mismatches, 0);
  page.fill(0, 0, 64); page.fill(255, 64, 128); page[128] = 0xfa;
  assert.equal(compareOemPage(page, decodeOemPage(page, 0), reference).mismatches, 0);
  const changed = decodeOemPage(page, 0); changed[2].power = 'altered';
  assert.throws(() => compareOemPage(page, changed, reference), /mismatch/);
});

test('observed USB reconstruction rejects missing bytes, bad addresses and checksums', () => {
  const stream = [81, 88, 6, ...new Array(16).fill(0)];
  for (let i = 0; i < 128; i++) {
    const address = 0x800000 + i * 16, payload = [address >>> 24, address >>> 16 & 255, address >>> 8 & 255, address & 255, 16, ...new Array(16).fill(i)];
    stream.push(87, ...payload, payload.reduce((a, b) => a + b, 0) & 255, 6);
  }
  stream.push(6);
  const received = new Map(stream.map((byte, index) => [index + 50, byte]));
  const page = pageFromReplies(received); assert.equal(page.length, 2048); assert.equal(page.at(-1), 127);
  received.delete(100); assert.throws(() => pageFromReplies(received), /Incomplete/);
  received.set(100, stream[50]); received.set(50 + 19 + 22, 0);
  assert.throws(() => pageFromReplies(received), /Invalid/);
});
