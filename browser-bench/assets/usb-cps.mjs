/* OpenD578 virtual USB wire for a future browser CPS.
 * This module never reads/writes the emulated memory, NAND or codeplug.
 * It only forwards host USB transactions to a *real* peripheral emulator.
 * Copyright (C) 2026 OpenD578 contributors. GPL-3.0-or-later.
 */
export class UsbNotConnected extends Error {
  constructor(message = 'Contrôleur USB GD32 non connecté au câble virtuel') {
    super(message);
    this.name = 'UsbNotConnected';
  }
}
function checkBytes(value, label, maxSize = 1024 * 1024) {
  if (!(value instanceof Uint8Array) || value.byteLength > maxSize) {
    throw new TypeError(`${label} : Uint8Array attendu, maximum ${maxSize} octets`);
  }
  return value;
}
function checkEp(ep) {
  if (!Number.isInteger(ep) || ep < 0 || ep > 15) throw new RangeError('Endpoint USB invalide');
  return ep;
}
/** Host-facing cable. The adapter must expose firmware-visible USB transactions.
 * No auto-answer, no synthetic codeplug, no direct backing-storage access.
 */
export class VirtualUsbCable {
  constructor() { this.device = null; }
  attachPeripheral(device) {
    if (!device || !['enumerate','control','out','in'].every(k=>typeof device[k] === 'function')) {
      throw new TypeError('Le périphérique USB doit fournir enumerate, control, out et in');
    }
    this.device = device;
  }
  disconnect() { this.device = null; }
  requireDevice() { if (!this.device) throw new UsbNotConnected(); return this.device; }
  async enumerate() { return this.requireDevice().enumerate(); }
  async control(setup, data = new Uint8Array()) {
    if (!(setup instanceof Uint8Array) || setup.length !== 8) throw new TypeError('SETUP USB doit faire 8 octets');
    return checkBytes(await this.requireDevice().control(setup.slice(),checkBytes(data,'control').slice()),'reponse control');
  }
  async bulkOut(endpoint, bytes) {
    checkEp(endpoint);
    const data=checkBytes(bytes,'bulk OUT');
    return this.requireDevice().out(endpoint, data.slice());
  }
  async bulkIn(endpoint, maxLength = 64) {
    checkEp(endpoint);
    if (!Number.isInteger(maxLength) || maxLength < 0 || maxLength > 1048576) throw new RangeError('Taille bulk IN invalide');
    return checkBytes(await this.requireDevice().in(endpoint,maxLength),'bulk IN',maxLength);
  }
}
/** Raw CPS transport only. A separate versioned CPS protocol must encode commands.
 * The peripheral implementing bulkOut/bulkIn is called; there is no fallback to memory.
 */
export class CpsUsbTransport {
  constructor(usbCable, { endpointOut, endpointIn } = {}) {
    if (!(usbCable instanceof VirtualUsbCable)) throw new TypeError('Câble USB virtuel obligatoire');
    this.usb=usbCable;
    this.endpointOut=checkEp(endpointOut);
    this.endpointIn=checkEp(endpointIn);
  }
  async exchange(request, maxResponse = 64) {
    await this.usb.bulkOut(this.endpointOut,checkBytes(request,'requête CPS'));
    return this.usb.bulkIn(this.endpointIn,maxResponse);
  }
}
