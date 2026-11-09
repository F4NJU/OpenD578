/* OpenD578 browser bench - bounded physical memory subset.
 * Copyright (C) 2026 OpenD578 contributors. GPL-3.0-or-later.
 */
export const FLASH_START = 0x08000000;
export const FLASH_SIZE = 3 * 1024 * 1024;
export const SRAM_START = 0x20000000;
export const SRAM_SIZE = 96 * 1024;
export const APPLICATION_DEFAULT = 0x08006000;

export class ModelBoundary extends Error {
  constructor(category, address, message) {
    super(message ?? `${category} @ 0x${(address >>> 0).toString(16).padStart(8, '0')}`);
    this.name = 'ModelBoundary';
    this.category = category;
    this.address = address >>> 0;
  }
}

export function parseAddress(value, fallback = APPLICATION_DEFAULT) {
  if (value === undefined || value === null || value === '') return fallback;
  const text = String(value).trim();
  if (!/^(?:0x[0-9a-f]+|[0-9]+)$/i.test(text)) throw new Error('Adresse invalide (hexadecimal 0x... ou decimal)');
  const parsed = Number(text);
  if (!Number.isSafeInteger(parsed) || parsed < 0 || parsed > 0xffffffff) throw new Error('Adresse hors plage 32 bits');
  return parsed >>> 0;
}

export function hex(value, width = 8) {
  return `0x${(value >>> 0).toString(16).toUpperCase().padStart(width, '0')}`;
}

export function checkVector(bytes, loadAddress) {
  const issues = [];
  if (!(bytes instanceof Uint8Array) || bytes.length < 8) {
    return { ok: false, stack: null, reset: null, issues: ['Image trop courte pour les vecteurs SP/Reset'] };
  }
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const stack = view.getUint32(0, true) >>> 0;
  const reset = view.getUint32(4, true) >>> 0;
  if (stack < SRAM_START || stack > SRAM_START + SRAM_SIZE || stack % 4 !== 0) issues.push('SP initial hors SRAM ou non aligne');
  if ((reset & 1) === 0) issues.push('Reset vector sans bit Thumb');
  const target = reset & ~1;
  const inFlash = target >= FLASH_START && target < FLASH_START + FLASH_SIZE;
  const inSram = target >= SRAM_START && target < SRAM_START + SRAM_SIZE;
  if (!inFlash && !inSram) issues.push('Adresse Reset non mappee');
  if (loadAddress % 128 !== 0) issues.push('VTOR non aligne sur 128 octets');
  return { ok: issues.length === 0, stack, reset, issues };
}

export class MemoryBus {
  constructor({ traceWrites = false } = {}) {
    this.traceWrites = !!traceWrites;
    this.flash = new Uint8Array(FLASH_SIZE);
    this.flash.fill(0xff);
    this.sram = new Uint8Array(SRAM_SIZE);
    this.flashImages = [];
    this.writes = [];
    this.writeCount = 0;
  }

  setTraceWrites(enabled) {
    this.traceWrites = !!enabled;
    if (!enabled) this.writes.length = 0;
  }

  loadFlash(bytes, address, role = 'firmware') {
    if (!(bytes instanceof Uint8Array)) throw new TypeError('Image Uint8Array attendue');
    const base = address >>> 0;
    if (base < FLASH_START || bytes.length > FLASH_SIZE || (base - FLASH_START) > FLASH_SIZE - bytes.length) {
      throw new Error(`${role}: taille/adresse hors Flash physique (3 Mio)`);
    }
    const offset = base - FLASH_START;
    const overlap = this.flashImages.filter(p => offset < p.offset + p.length && p.offset < offset + bytes.length);
    this.flash.set(bytes, offset);
    const entry = { role, address: base, length: bytes.length, offset, overlaps: overlap.map(p => p.role) };
    this.flashImages.push(entry);
    return entry;
  }

  region(address, size = 1, write = false) {
    const a = address >>> 0;
    if (!Number.isSafeInteger(address) || address < 0 || address > 0xffffffff) {
      throw new ModelBoundary('physical_address_unmapped', a);
    }
    if (size < 1 || size > 4096 || a + size > 0x100000000) {
      throw new ModelBoundary('physical_address_unmapped', a, 'Acces traversant une limite physique');
    }
    if (a >= SRAM_START && a + size <= SRAM_START + SRAM_SIZE) {
      return { data: this.sram, offset: a - SRAM_START, address: a };
    }
    if ((a >= FLASH_START && a + size <= FLASH_START + FLASH_SIZE) ||
        (a < FLASH_SIZE && a + size <= FLASH_SIZE)) {
      if (write) throw new ModelBoundary('model_incomplete', a, 'Programmation Flash non implementee dans le banc navigateur');
      const offset = a >= FLASH_START ? a - FLASH_START : a;
      return { data: this.flash, offset, address: a };
    }
    throw new ModelBoundary('model_incomplete', a, `Peripherique non modele : ${hex(a)}`);
  }

  read8(address) { const r = this.region(address); return r.data[r.offset]; }
  read16(address) {
    if ((address & 1) !== 0) throw new ModelBoundary('execution_boundary', address, 'Lecture 16 bits non alignee');
    const r = this.region(address, 2);
    return r.data[r.offset] | (r.data[r.offset + 1] << 8);
  }
  read32(address) {
    if ((address & 3) !== 0) throw new ModelBoundary('execution_boundary', address, 'Lecture 32 bits non alignee');
    const r = this.region(address, 4);
    return (r.data[r.offset] | (r.data[r.offset + 1] << 8) | (r.data[r.offset + 2] << 16) | (r.data[r.offset + 3] << 24)) >>> 0;
  }
  readBlock(address, length) {
    if (!Number.isInteger(length) || length < 1 || length > 256) throw new Error('Inspection limitee a 256 octets');
    const r = this.region(address, length);
    return r.data.slice(r.offset, r.offset + length);
  }
  write8(address, value) { this.writeBytes(address, Uint8Array.of(value & 255)); }
  write16(address, value) {
    if ((address & 1) !== 0) throw new ModelBoundary('execution_boundary', address, 'Ecriture 16 bits non alignee');
    this.writeBytes(address, Uint8Array.of(value & 255, (value >>> 8) & 255));
  }
  write32(address, value) {
    if ((address & 3) !== 0) throw new ModelBoundary('execution_boundary', address, 'Ecriture 32 bits non alignee');
    this.writeBytes(address, Uint8Array.of(value & 255, (value >>> 8) & 255, (value >>> 16) & 255, (value >>> 24) & 255));
  }
  writeBytes(address, bytes) {
    const r = this.region(address, bytes.length, true);
    r.data.set(bytes, r.offset);
    this.writeCount++;
    if (this.traceWrites) {
      if (this.writes.length >= 128) this.writes.shift();
      this.writes.push({ address: address >>> 0, width: bytes.length, value: [...bytes].map(b => b.toString(16).padStart(2, '0')).join('') });
    }
  }
}
