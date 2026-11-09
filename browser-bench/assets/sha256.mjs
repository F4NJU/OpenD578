/* Streaming SHA-256 (no CDN and no whole-256-MiB read into RAM).
 * Copyright (C) 2026 OpenD578 contributors. GPL-3.0-or-later.
 */
const K = new Uint32Array([
  0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
  0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
  0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
  0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
  0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
  0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
  0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
  0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
]);
const INITIAL = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
const rotr = (n,s) => (n>>>s)|(n<<(32-s));
export class SHA256 {
  constructor() { this.h = new Uint32Array(INITIAL); this.buf = new Uint8Array(64); this.len = 0; this.total = 0n; this.done = false; }
  transform(block) {
    const w = new Uint32Array(64);
    for (let i = 0; i < 16; i++) { const j=i*4; w[i] = (block[j]<<24 | block[j+1]<<16 | block[j+2]<<8 | block[j+3]) >>> 0; }
    for (let i = 16; i < 64; i++) {
      const x=w[i-15], y=w[i-2];
      w[i] = (w[i-16] + (rotr(x,7)^rotr(x,18)^(x>>>3)) + w[i-7] + (rotr(y,17)^rotr(y,19)^(y>>>10))) >>> 0;
    }
    let [a,b,c,d,e,f,g,h] = this.h;
    for (let i=0;i<64;i++) {
      const s1=rotr(e,6)^rotr(e,11)^rotr(e,25);
      const t1=(h+s1+((e&f)^(~e&g))+K[i]+w[i])>>>0;
      const s0=rotr(a,2)^rotr(a,13)^rotr(a,22);
      const t2=(s0+((a&b)^(a&c)^(b&c)))>>>0;
      h=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;
    }
    const v=[a,b,c,d,e,f,g,h];
    for (let i=0;i<8;i++) this.h[i] = (this.h[i]+v[i])>>>0;
  }
  update(bytes) {
    if (this.done) throw new Error('SHA256 finalise');
    if (!(bytes instanceof Uint8Array)) throw new TypeError('Uint8Array attendu');
    this.total += BigInt(bytes.length);
    let i=0;
    if (this.len) {
      const count=Math.min(64-this.len,bytes.length);
      this.buf.set(bytes.subarray(0,count),this.len);this.len+=count;i+=count;
      if (this.len===64) { this.transform(this.buf);this.len=0; }
    }
    for (;i+64<=bytes.length;i+=64) this.transform(bytes.subarray(i,i+64));
    if (i<bytes.length) { this.buf.set(bytes.subarray(i),0);this.len=bytes.length-i; }
    return this;
  }
  hex() {
    if (this.done) throw new Error('SHA256 deja finalise');
    const bits = this.total*8n;
    this.update(Uint8Array.of(0x80));
    const pad = (56 - this.len + 64) % 64;
    if (pad) this.update(new Uint8Array(pad));
    const tail=new Uint8Array(8);
    for (let i=0;i<8;i++) tail[7-i]=Number((bits >> BigInt(i*8)) & 255n);
    this.update(tail);
    this.done = true;
    return Array.from(this.h,h=>h.toString(16).padStart(8,'0')).join('');
  }
}
export async function sha256File(file, progress = null, chunkSize = 1024*1024) {
  const hash=new SHA256();
  for (let start=0;start<file.size;start+=chunkSize) {
    const end=Math.min(file.size,start+chunkSize);
    hash.update(new Uint8Array(await file.slice(start,end).arrayBuffer()));
    if (progress) progress(end,file.size);
  }
  return hash.hex();
}
