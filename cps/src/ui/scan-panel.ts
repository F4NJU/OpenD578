import type { Codeplug, ScanList } from '../core/model.ts';
import { moveItem } from '../core/editor.ts';
import { formatMHz } from '../core/frequency.ts';

const scanDialog = document.querySelector<HTMLDialogElement>('#scan-dialog')!;
const scanEscape = (value: unknown): string => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]!);
let scanDraft: ScanList | null = null;

export function openScanPanel(getValue: () => Codeplug, save: (value: Codeplug) => void): void {
  scanDraft = null;

  function shell(body: string): void {
    scanDialog.innerHTML = `<div class="dialog-head"><h2 id="scan-title">Listes de scan</h2><button type="button" data-scan="close" aria-label="Fermer">×</button></div><div class="dialog-body"><p class="help">Préparation hors ligne : membres ordonnés et priorité optionnelle. Le comportement du scan sur le firmware reste à convenir avec F4EGM.</p><div id="scan-error" class="notice error" role="alert" hidden></div>${body}</div>`;
  }
  function overview(): void {
    scanDraft = null;
    const value = getValue();
    shell(`<div class="toolbar"><span>${value.scanLists.length} liste(s)</span><button type="button" data-scan="new" class="primary">＋ Liste de scan</button></div>${value.scanLists.length ? `<div class="table-scroll"><table aria-label="Listes de scan"><thead><tr><th>Nom</th><th>Membres</th><th>Priorité</th><th>Actions</th></tr></thead><tbody>${value.scanLists.map(list => `<tr><td>${scanEscape(list.name)}</td><td>${list.channelIds.length}</td><td>${scanEscape(value.channels.find(channel => channel.id === list.priorityChannelId)?.name ?? 'Aucune')}</td><td><button type="button" data-scan="edit" data-id="${scanEscape(list.id)}">Modifier</button> <button type="button" data-scan="delete" data-id="${scanEscape(list.id)}" class="danger">Supprimer</button></td></tr>`).join('')}</tbody></table></div>` : '<p>Aucune liste de scan. Créez-en une à partir de vos canaux existants.</p>'}`);
  }
  function rememberFields(): void {
    if (!scanDraft) return;
    const name = scanDialog.querySelector<HTMLInputElement>('[name="scan-name"]');
    const priority = scanDialog.querySelector<HTMLSelectElement>('[name="priority"]');
    if (name && priority) scanDraft = { ...scanDraft, name: name.value, priorityChannelId: priority.value || null };
  }
  function edit(): void {
    const value = getValue(), list = scanDraft!;
    const members = list.channelIds.map(id => value.channels.find(channel => channel.id === id)!);
    shell(`<form id="scan-form"><div class="form-grid">${`<label class="field full">Nom de la liste<input name="scan-name" value="${scanEscape(list.name)}" required></label>`}<label class="field full">Canal prioritaire<select name="priority"><option value="">Aucun</option>${members.map(channel => `<option value="${scanEscape(channel.id)}" ${channel.id === list.priorityChannelId ? 'selected' : ''}>${scanEscape(channel.name)}</option>`).join('')}</select></label></div>
      <h3>Membres · ordre du scan</h3>${members.length ? `<div class="table-scroll"><table aria-label="Membres ordonnés"><tbody>${members.map((channel, index) => `<tr><td>${index + 1}</td><td>${scanEscape(channel.name)}</td><td class="freq">${formatMHz(channel.rxHz)}</td><td><button type="button" data-scan="up" data-id="${scanEscape(channel.id)}" aria-label="Monter ${scanEscape(channel.name)}" ${index === 0 ? 'disabled' : ''}>↑</button> <button type="button" data-scan="down" data-id="${scanEscape(channel.id)}" aria-label="Descendre ${scanEscape(channel.name)}" ${index === members.length - 1 ? 'disabled' : ''}>↓</button></td></tr>`).join('')}</tbody></table></div>` : '<p class="help">Une liste vide peut être préparée puis complétée.</p>'}
      <h3>Choisir les canaux</h3><div class="member-list">${value.channels.length ? value.channels.map(channel => `<label class="check-label"><input type="checkbox" data-scan-member="${scanEscape(channel.id)}" ${list.channelIds.includes(channel.id) ? 'checked' : ''}>${scanEscape(channel.name)} <span class="freq">${formatMHz(channel.rxHz)}</span></label>`).join('') : '<p class="help">Créez d’abord des canaux dans l’éditeur.</p>'}</div><div class="dialog-footer"><button type="button" data-scan="back">Annuler</button><button type="submit" class="primary">Enregistrer la liste</button></div></form>`);
    scanDialog.querySelector('form')!.addEventListener('submit', event => {
      event.preventDefault(); rememberFields();
      try {
        const current = getValue(), draft = { ...scanDraft!, name: scanDraft!.name.trim() };
        const exists = current.scanLists.some(item => item.id === draft.id);
        save({ ...current, scanLists: exists ? current.scanLists.map(item => item.id === draft.id ? draft : item) : [...current.scanLists, draft] });
        overview();
      } catch (error) { showError(error); }
    });
  }
  function showError(error: unknown): void {
    const box = scanDialog.querySelector<HTMLDivElement>('#scan-error')!;
    box.hidden = false; box.textContent = (error as Error).message;
  }
  scanDialog.onclick = event => {
    const button = (event.target as HTMLElement).closest<HTMLButtonElement>('[data-scan]');
    if (!button || button.disabled) return;
    const action = button.dataset.scan, id = button.dataset.id!;
    try {
      if (action === 'close') { scanDialog.close(); scanDraft = null; }
      else if (action === 'back') overview();
      else if (action === 'new') { scanDraft = { id: `scan-${crypto.randomUUID()}`, name: 'Nouvelle liste', channelIds: [], priorityChannelId: null }; edit(); }
      else if (action === 'edit') { scanDraft = structuredClone(getValue().scanLists.find(list => list.id === id)!); edit(); }
      else if (action === 'delete' && confirm('Supprimer cette liste ? Les canaux seront conservés.')) { save({ ...getValue(), scanLists: getValue().scanLists.filter(list => list.id !== id) }); overview(); }
      else if ((action === 'up' || action === 'down') && scanDraft) {
        rememberFields(); scanDraft = { ...scanDraft!, channelIds: moveItem(scanDraft!.channelIds, scanDraft!.channelIds.indexOf(id), action === 'up' ? -1 : 1) }; edit();
      }
    } catch (error) { showError(error); }
  };
  scanDialog.onchange = event => {
    const input = event.target as HTMLInputElement, id = input.dataset.scanMember;
    if (!id || !scanDraft) return;
    rememberFields();
    scanDraft = { ...scanDraft!, channelIds: input.checked ? [...scanDraft!.channelIds, id] : scanDraft!.channelIds.filter(item => item !== id),
      priorityChannelId: !input.checked && scanDraft!.priorityChannelId === id ? null : scanDraft!.priorityChannelId };
    edit();
  };
  overview(); scanDialog.showModal();
}
scanDialog.addEventListener('close', () => { scanDraft = null; });
window.addEventListener('beforeunload', event => { if (scanDialog.open && scanDraft) { event.preventDefault(); event.returnValue = ''; } });
