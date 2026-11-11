/** PC file contract only. No OEM addresses or calibration data belong here. */
export interface AnalogSettings {
  mode: 'FM';
  rxHz: number;
  txHz: number;
  bandwidth: 'narrow' | 'wide';
  power: string;
  rxCtcssDeciHz: number | null;
  txCtcssDeciHz: number | null;
  txInhibit: boolean;
}

export interface Channel extends AnalogSettings {
  id: string;
  name: string;
}

export interface Zone {
  id: string;
  name: string;
  channelIds: string[];
}

export interface ScanList {
  id: string;
  name: string;
  channelIds: string[];
  priorityChannelId: string | null;
}

export interface Codeplug {
  format: 'opend578-codeplug';
  schemaVersion: 2;
  name: string;
  channels: Channel[];
  zones: Zone[];
  scanLists: ScanList[];
  vfo: AnalogSettings | null;
}

/** Capabilities are supplied by a future device adapter, never inferred from OEM. */
export interface DeviceCapabilities {
  maxChannels: number;
  maxZones: number;
  maxChannelsPerZone: number;
  maxNameBytes: number;
  rxBands: { minHz: number; maxHz: number }[];
  txBands: { minHz: number; maxHz: number }[];
  bandwidths: ('narrow' | 'wide')[];
  powerLevels: string[];
  ctcssDeciHz: number[];
  supportsVfo: boolean;
  maxScanLists?: number;
  maxChannelsPerScanList?: number;
  supportsScanPriority?: boolean;
}

export interface ValidationIssue {
  path: string;
  code: string;
  message: string;
}

export function createCodeplug(name = 'Nouveau codeplug'): Codeplug {
  return {
    format: 'opend578-codeplug', schemaVersion: 2, name,
    channels: [], zones: [], scanLists: [], vfo: null,
  };
}
