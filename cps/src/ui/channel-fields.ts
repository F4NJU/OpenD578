import type { AnalogSettings } from '../core/model.ts';
import { formatMHz, parseMHz } from '../core/frequency.ts';
import { txFromOffset } from '../core/channel-tools.ts';

const fieldEscape = (value: string): string => value.replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]!);
function nonnegativeMHz(value: string): number {
  return /^0+(?:[.,]0{1,6})?$/.test(value.trim()) ? 0 : parseMHz(value);
}
export function frequencyFields(value: AnalogSettings): string {
  const difference = value.txHz - value.rxHz, direction = difference === 0 ? 'simplex' : difference > 0 ? 'plus' : 'minus';
  return `<label class="field">Réception · MHz<input name="rx" value="${formatMHz(value.rxHz)}" required inputmode="decimal"></label>
    <label class="field">Émission · MHz<input name="tx" value="${formatMHz(value.txHz)}" required inputmode="decimal"></label>
    <label class="field">Décalage relais<select name="shift-mode">${[['direct', 'TX indépendante'], ['simplex', 'Simplex'], ['plus', '+ Décalage positif'], ['minus', '− Décalage négatif']].map(([id, label]) => `<option value="${id}" ${direction === id ? 'selected' : ''}>${label}</option>`).join('')}</select></label>
    <label class="field">Valeur du décalage · MHz<input name="shift-value" value="${difference === 0 ? '0.600000' : formatMHz(Math.abs(difference))}" inputmode="decimal" required></label>
    <p class="help full">En mode décalage, TX suit RX automatiquement. Choisissez « TX indépendante » pour saisir TX directement. Seules les fréquences RX/TX sont enregistrées.</p>`;
}
export function readFrequencies(data: FormData): { rxHz: number; txHz: number } {
  const rxHz = parseMHz(String(data.get('rx'))), mode = String(data.get('shift-mode'));
  if (mode === 'direct') return { rxHz, txHz: parseMHz(String(data.get('tx'))) };
  return { rxHz, txHz: txFromOffset(rxHz, mode as 'simplex' | 'plus' | 'minus', mode === 'simplex' ? 0 : nonnegativeMHz(String(data.get('shift-value')))) };
}
export function powerField(current: string, extras: string[] = [], keep = false): string {
  const levels = [...new Set(['low', 'medium', 'high', 'turbo', ...extras, ...(current ? [current] : [])])];
  return `<label class="field">Niveau de puissance<select name="power-choice">${keep ? '<option value="keep">Conserver</option>' : ''}${levels.map(level => `<option value="value:${fieldEscape(level)}" ${!keep && level === current ? 'selected' : ''}>${fieldEscape(level)}</option>`).join('')}<option value="custom">Personnalisé…</option></select></label>
    <label class="field" data-custom-power hidden>Identifiant personnalisé<input name="power-custom" placeholder="Ex. niveau-association" disabled></label>
    <p class="help full">Ces identifiants n’impliquent aucune puissance en watts ni disponibilité sur le poste ; le firmware devra annoncer ses niveaux.</p>`;
}
export function readPower(data: FormData): string {
  const choice = String(data.get('power-choice'));
  if (choice === 'keep') return '';
  const value = choice === 'custom' ? String(data.get('power-custom') ?? '').trim() : choice.startsWith('value:') ? choice.slice(6) : '';
  if (!value) throw new Error('Indiquez un niveau de puissance.');
  return value;
}
export function bindChannelFields(container: HTMLElement): void {
  const power = container.querySelector<HTMLSelectElement>('[name="power-choice"]');
  if (power) {
    const update = (): void => { const custom = container.querySelector<HTMLElement>('[data-custom-power]')!, input = custom.querySelector<HTMLInputElement>('input')!; custom.hidden = power.value !== 'custom'; input.disabled = custom.hidden; input.required = !custom.hidden; };
    power.addEventListener('change', update); update();
  }
  const mode = container.querySelector<HTMLSelectElement>('[name="shift-mode"]');
  if (!mode) return;
  const tx = container.querySelector<HTMLInputElement>('[name="tx"]')!, offset = container.querySelector<HTMLInputElement>('[name="shift-value"]')!;
  const update = (): void => {
    tx.readOnly = mode.value !== 'direct'; offset.disabled = mode.value === 'direct' || mode.value === 'simplex'; tx.setCustomValidity('');
    if (mode.value === 'direct') return;
    try { tx.value = formatMHz(readFrequencies(new FormData(container.querySelector('form')!)).txHz); }
    catch (error) { tx.setCustomValidity((error as Error).message); }
  };
  for (const name of ['rx', 'shift-value', 'shift-mode']) container.querySelector(`[name="${name}"]`)!.addEventListener('input', update);
  mode.addEventListener('change', update); update();
}
