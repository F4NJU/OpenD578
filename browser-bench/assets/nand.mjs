/* Read-only source files with an explicit, volatile NAND overlay.
 * Logical main / OOB / ECC captures remain separate. Protocol and ECC decoding
 * are intentionally NOT modeled by this storage layer.
 * Copyright (C) 2026 OpenD578 contributors. GPL-3.0-or-later.
 */
export const NAND_PAGE = 2048;
export const NAND_PAGES_PER_BLOCK = 64;
export const NAND_PAGES = 131072;
export const NAND_MAIN_SIZE = NAND_PAGES * NAND_PAGE;
export const NAND_OOB_PAGE = 64;
export const NAND_OOB_SIZE = NAND_PAGES * NAND_OOB_PAGE;
export const NAND_ECC_SIZE = NAND_PAGES;
export const NAND_SCHEMA = 'opend578.nand-overlay.v1';

const ZONES = Object.freeze({ main: NAND_PAGE, oob: NAND_OOB_PAGE, ecc: 1 });
const ZONE_SIZES = Object.freeze({ main: NAND_MAIN_SIZE, oob: NAND_OOB_SIZE, ecc: NAND_ECC_SIZE });
function validInt(n, min, max, name) {
  if (!Number.isInteger(n) || n < min || n > max) throw new Error(`${name} hors plage (${min}..${max})`);
  return n;
}
function encodeBytes(bytes) { return btoa(String.fromCharCode(...bytes)); }
function decodeBytes(str, expected) {
  if (typeof str !== 'string' || str.length > 4096 || !/^[A-Za-z0-9+/]*={0,2}$/.test(str)) throw new Error('Base64 invalide');
  const raw = atob(str);
  if (raw.length !== expected) throw new Error('Taille page du correctif invalide');
  return Uint8Array.from(raw, char => char.charCodeAt(0));
}

export class NandOverlay {
  constructor({syncReader=null}={}) {
    this.syncReader=syncReader;
    this.files = { main: null, oob: null, ecc: null };
    this.overlay = new Map();
    this.programOps = 0;
    this.eraseOps = 0;
  }
  attach(zone, file) {
    if (!Object.hasOwn(ZONES, zone)) throw new Error('Zone NAND inconnue');
    if (file !== null && file.size !== ZONE_SIZES[zone]) {
      throw new Error(`${zone} : ${file.size} octets, attendu ${ZONE_SIZES[zone]} (pas de troncature/supposition)`);
    }
    this.files[zone] = file;
    for (const key of this.overlay.keys()) if (key.startsWith(`${zone}:`)) this.overlay.delete(key);
  }
  key(zone, page) {
    if (!Object.hasOwn(ZONES, zone)) throw new Error('Zone NAND inconnue');
    validInt(page, 0, NAND_PAGES - 1, 'Page NAND');
    return `${zone}:${page}`;
  }
  async readPage(zone, page) {
    const key = this.key(zone, page);
    const modified = this.overlay.get(key);
    if (modified) return { bytes: modified.slice(), source: 'overlay' };
    const count = ZONES[zone], file = this.files[zone];
    if (!file) throw new Error('Capture NAND absente : '+zone+' ; aucune donnée de remplacement autorisée');
    const chunk = new Uint8Array(await file.slice(page * count, (page + 1) * count).arrayBuffer());
    if (chunk.length !== count) throw new Error('Lecture NAND tronquee');
    return { bytes: chunk, source: 'fichier local' };
  }
  // Worker-only synchronous path for the CPU's bit-banged NAND transactions.
  // FileReaderSync exists inside Dedicated Workers and reads just one 2KiB/64B page.
  // No eager 256MiB allocation, no asynchronous response fabricated mid-instruction.
  readPageSync(zone, page) {
    const key=this.key(zone,page),modified=this.overlay.get(key);
    if(modified)return {bytes:modified.slice(),source:'overlay'};
    const count=ZONES[zone],file=this.files[zone];
    if(!file)throw new Error('Capture NAND absente : '+zone+' ; aucune donnée de remplacement autorisée');
    let bytes;
    if(this.syncReader) bytes=this.syncReader(file,page*count,(page+1)*count);
    else if(typeof FileReaderSync!=='undefined') bytes=new Uint8Array(new FileReaderSync().readAsArrayBuffer(file.slice(page*count,(page+1)*count)));
    else throw new Error('Lecture NAND synchrone impossible: emulation CPU exige un Web Worker avec FileReaderSync');
    if(!(bytes instanceof Uint8Array)||bytes.length!==count)throw new Error('Lecture NAND physique tronquee');
    return {bytes:bytes.slice(),source:'fichier local'};
  }
  programSync(zone, page, offset, bytes) {
    if(zone==='ecc')throw new Error('ECC en lecture seule');
    if(!(bytes instanceof Uint8Array)||bytes.length<1||offset<0||offset+bytes.length>ZONES[zone])throw new Error('Donnees NAND hors page');
    const next=this.readPageSync(zone,page).bytes;
    for(let i=0;i<bytes.length;i++)next[offset+i]&=bytes[i];
    this.overlay.set(this.key(zone,page),next);this.programOps++;
    return next;
  }
  eraseSync(block) {
    validInt(block,0,NAND_PAGES/NAND_PAGES_PER_BLOCK-1,'Bloc NAND');
    for(let i=0;i<NAND_PAGES_PER_BLOCK;i++)for(const zone of ['main','oob']){
      this.overlay.set(this.key(zone,block*NAND_PAGES_PER_BLOCK+i),new Uint8Array(ZONES[zone]).fill(0xff));
    }
    this.eraseOps++;
  }
  async program(zone, page, offset, bytes) {
    if (zone === 'ecc') throw new Error('Le fichier ECC est un statut brut; aucune ecriture interpretee');
    if (!(bytes instanceof Uint8Array) || bytes.length < 1 || bytes.length > 128) throw new Error('Ecriture limitee a 1..128 octets');
    validInt(offset, 0, ZONES[zone] - bytes.length, 'Offset page');
    const entry = await this.readPage(zone, page);
    const next = entry.bytes;
    for (let i = 0; i < bytes.length; i++) {
      const prior = next[offset + i];
      if ((prior & bytes[i]) !== bytes[i]) {
        throw new Error(`Programmation 0->1 interdite (page ${page}, octet ${offset + i}); effacer bloc d'abord`);
      }
    }
    for (let i = 0; i < bytes.length; i++) next[offset + i] &= bytes[i];
    this.overlay.set(this.key(zone, page), next);
    this.programOps++;
    return { bytes: next.slice(), source: 'overlay' };
  }
  async erase(block) {
    validInt(block, 0, NAND_PAGES / NAND_PAGES_PER_BLOCK - 1, 'Bloc NAND');
    for (let i = 0; i < NAND_PAGES_PER_BLOCK; i++) {
      const page = block * NAND_PAGES_PER_BLOCK + i;
      this.overlay.set(this.key('main', page), new Uint8Array(NAND_PAGE).fill(0xff));
      this.overlay.set(this.key('oob', page), new Uint8Array(NAND_OOB_PAGE).fill(0xff));
    }
    this.eraseOps++;
    return { block, pages: NAND_PAGES_PER_BLOCK, warning: 'Effacement logique idealise. Pas de simulation de wear, bad blocks, ECC ou timings.' };
  }
  summary() {
    return {
      geometry: { pages: NAND_PAGES, bytesPerPage: NAND_PAGE, oobBytesPerPage: NAND_OOB_PAGE, pagesPerBlock: NAND_PAGES_PER_BLOCK },
      captures: Object.fromEntries(Object.entries(this.files).map(([k, f]) => [k, f ? { name: f.name, size: f.size } : null])),
      overlayPages: this.overlay.size,
      programOps: this.programOps,
      eraseOps: this.eraseOps
    };
  }
  exportPatch() {
    // Prevent accidental exporting of huge sets (and inadvertent sharing of proprietary data).
    if (this.overlay.size > 4096) throw new Error('Correctif trop volumineux (maximum 4096 pages modifiees)');
    return {
      schema: NAND_SCHEMA,
      warning: 'Peut contenir des octets issus des captures personnelles. Ne pas publier sans revue.',
      geometry: { page: NAND_PAGE, oob: NAND_OOB_PAGE, pagesPerBlock: NAND_PAGES_PER_BLOCK },
      changes: Array.from(this.overlay, ([key, bytes]) => {
        const [zone, page] = key.split(':');
        return { zone, page: Number(page), base64: encodeBytes(bytes) };
      }).sort((a, b) => a.zone.localeCompare(b.zone) || a.page - b.page)
    };
  }
  importPatch(patch) {
    if (!patch || patch.schema !== NAND_SCHEMA || !Array.isArray(patch.changes) || patch.changes.length > 4096) {
      throw new Error('Correctif NAND incompatible');
    }
    if (patch.geometry?.page !== NAND_PAGE || patch.geometry?.oob !== NAND_OOB_PAGE ||
        patch.geometry?.pagesPerBlock !== NAND_PAGES_PER_BLOCK) throw new Error('Geometrie NAND incorrecte');
    const pending = new Map();
    for (const entry of patch.changes) {
      const key = this.key(entry.zone, entry.page);
      if (pending.has(key)) throw new Error('Page duplicatee dans le correctif');
      pending.set(key, decodeBytes(entry.base64, ZONES[entry.zone]));
    }
    // Atomic replacement: invalid patches must not change the current overlay.
    this.overlay = pending;
    return { importedPages: pending.size };
  }
}
