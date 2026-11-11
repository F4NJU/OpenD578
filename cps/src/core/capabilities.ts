import type { AnalogSettings, DeviceCapabilities, ValidationIssue } from './model.ts';
import { validateCodeplug } from './validation.ts';
import type { Codeplug } from './model.ts';

function inBands(hz: number, bands: DeviceCapabilities['rxBands']): boolean {
  return bands.some(({ minHz, maxHz }) => hz >= minHz && hz <= maxHz);
}

/** Run after validating the adapter's capabilities; does not authorize a transfer. */
export function validateForDevice(codeplug: Codeplug, capabilities: DeviceCapabilities): ValidationIssue[] {
  const issues = validateCodeplug(codeplug);
  if (issues.length) return issues;
  const add = (path: string, message: string): void => {
    issues.push({ path, code: 'device_capability', message });
  };
  const checkName = (name: string, path: string): void => {
    if (new TextEncoder().encode(name).length > capabilities.maxNameBytes) add(path, 'Nom trop long en octets UTF-8 pour ce poste.');
  };
  const checkSettings = (settings: AnalogSettings, path: string): void => {
    if (!inBands(settings.rxHz, capabilities.rxBands)) add(`${path}.rxHz`, 'Fréquence hors bandes RX du poste.');
    if (!settings.txInhibit && !inBands(settings.txHz, capabilities.txBands)) add(`${path}.txHz`, 'Fréquence hors bandes TX du poste.');
    if (!capabilities.bandwidths.includes(settings.bandwidth)) add(`${path}.bandwidth`, 'Largeur FM non prise en charge.');
    if (!capabilities.powerLevels.includes(settings.power)) add(`${path}.power`, 'Niveau de puissance inconnu du poste.');
    for (const field of ['rxCtcssDeciHz', 'txCtcssDeciHz'] as const) {
      const tone = settings[field];
      if (tone !== null && !capabilities.ctcssDeciHz.includes(tone)) add(`${path}.${field}`, 'CTCSS non pris en charge.');
    }
  };
  if (codeplug.channels.length > capabilities.maxChannels) add('$.channels', 'Trop de canaux pour ce poste.');
  if (codeplug.zones.length > capabilities.maxZones) add('$.zones', 'Trop de zones pour ce poste.');
  codeplug.channels.forEach((channel, index) => {
    checkName(channel.name, `$.channels[${index}].name`);
    checkSettings(channel, `$.channels[${index}]`);
  });
  codeplug.zones.forEach((zone, index) => {
    checkName(zone.name, `$.zones[${index}].name`);
    if (zone.channelIds.length > capabilities.maxChannelsPerZone) add(`$.zones[${index}].channelIds`, 'Trop de canaux dans cette zone.');
  });
  if (codeplug.vfo !== null) {
    if (!capabilities.supportsVfo) add('$.vfo', 'Programmation du VFO non prise en charge.');
    checkSettings(codeplug.vfo, '$.vfo');
  }
  return issues;
}
