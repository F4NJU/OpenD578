import type { AnalogSettings, Channel, Codeplug, Zone } from '../core/model.ts';
import { createCodeplug } from '../core/model.ts';
import { parseCodeplug, serializeCodeplug } from '../core/json.ts';
import { parseMHz, formatMHz } from '../core/frequency.ts';
import { parseChannelsCsv, serializeChannelsCsv } from '../core/csv.ts';
import { EditorHistory, appendChannels, deleteChannels, moveItem } from '../core/editor.ts';
import { openBenchPanel } from './bench-panel.ts';

const STORAGE_KEY = 'opend578.cps.editor.v1';
const root = document.querySelector<HTMLDivElement>('#app')!;
const dialog = document.querySelector<HTMLDialogElement>('#editor-dialog')!;
const fileInput = document.querySelector<HTMLInputElement>('#file-input')!;
const escapeHtml = (value: unknown): string => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]!);
let notice = '', isError = false, storageProblem = false;
let exportedSnapshot = serializeCodeplug(createCodeplug());
let initial = createCodeplug();
try {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    const saved = JSON.parse(stored);
    initial = parseCodeplug(JSON.stringify(saved.codeplug));
    exportedSnapshot = typeof saved.exportedSnapshot === 'string' ? saved.exportedSnapshot : '';
    notice = 'Votre dernière session a été restaurée.';
  }
} catch { notice = 'La session locale est indisponible ou invalide. Importez votre fichier JSON ; les anciennes données locales ne sont pas effacées.'; isError = true; storageProblem = true; }
const history = new EditorHistory(initial);
let activeZone: string | null = null, query = '';
let selected = new Set<string>();

function persist(): void {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify({ codeplug: history.value, exportedSnapshot })); storageProblem = false; }
  catch { storageProblem = true; }
}
function dirty(): boolean { return serializeCodeplug(history.value) !== exportedSnapshot; }
function commit(next: Codeplug, message = 'Modifications enregistrées dans la session.'): void {
  history.commit(next); persist(); notice = message; isError = false; render();
}
function fail(error: unknown): void { notice = error instanceof Error ? error.message : String(error); isError = true; render(); }
function newId(prefix: string): string { return `${prefix}-${crypto.randomUUID()}`; }
function defaults(): AnalogSettings {
  return { mode: 'FM', rxHz: 145500000, txHz: 145500000, bandwidth: 'narrow', power: 'low', rxCtcssDeciHz: null, txCtcssDeciHz: null, txInhibit: true };
}
function visibleChannels(value: Codeplug): Channel[] {
  const zone = value.zones.find(item => item.id === activeZone);
  const ordered = zone ? zone.channelIds.map(id => value.channels.find(channel => channel.id === id)!) : value.channels;
  const term = query.toLocaleLowerCase('fr');
  return ordered.filter(channel => `${channel.name} ${formatMHz(channel.rxHz)} ${formatMHz(channel.txHz)}`.toLocaleLowerCase('fr').includes(term));
}
function toneText(value: number | null): string { return value === null ? '—' : (value / 10).toFixed(1); }
function checked(value: boolean): string { return value ? 'checked' : ''; }
function disabled(value: boolean): string { return value ? 'disabled' : ''; }

function sidebar(value: Codeplug): string {
  return `<aside><section><p class="eyebrow">Bibliothèque</p><nav class="nav" aria-label="Codeplug">
    <button data-action="all" class="${activeZone === null ? 'active' : ''}" ${activeZone === null ? 'aria-current="page"' : ''}>Tous les canaux <span class="count">${value.channels.length}</span></button>
    <button data-action="vfo">Réglages VFO <span class="count">${value.vfo ? 'FM' : '—'}</span></button></nav></section>
    <section><p class="eyebrow">Zones · ${value.zones.length}</p><nav class="nav" aria-label="Zones">${value.zones.map(zone => `<button data-action="zone" data-id="${escapeHtml(zone.id)}" class="${activeZone === zone.id ? 'active' : ''}" ${activeZone === zone.id ? 'aria-current="page"' : ''}><span>${escapeHtml(zone.name)}</span><span class="count">${zone.channelIds.length}</span></button>`).join('')}</nav>
    <div class="aside-actions"><button data-action="new-zone">＋ Nouvelle zone</button></div></section>
    <div class="aside-note"><strong>Votre codeplug reste ici.</strong>Les fichiers sont traités sur ce PC. Exportez un JSON pour conserver une sauvegarde complète.</div></aside>`;
}
function channelRow(channel: Channel, index: number): string {
  const id = escapeHtml(channel.id);
  return `<tr class="${selected.has(channel.id) ? 'selected' : ''}">
    <td><input type="checkbox" data-select="${id}" aria-label="Sélectionner ${escapeHtml(channel.name)}" ${checked(selected.has(channel.id))}></td>
    <td class="freq">${String(index + 1).padStart(2, '0')}</td>
    <td><button class="channel-name" data-action="edit" data-id="${id}">${escapeHtml(channel.name)}</button></td>
    <td class="freq">${formatMHz(channel.rxHz)}</td><td class="freq">${formatMHz(channel.txHz)}</td>
    <td class="freq">${toneText(channel.rxCtcssDeciHz)} / ${toneText(channel.txCtcssDeciHz)}</td>
    <td>${channel.bandwidth === 'narrow' ? 'Étroite' : 'Large'}</td><td>${escapeHtml(channel.power)}</td>
    <td><span class="tag ${channel.txInhibit ? '' : 'tx'}">${channel.txInhibit ? 'RX seul' : 'RX / TX'}</span></td>
    <td><button class="icon" data-action="up" data-id="${id}" aria-label="Monter ${escapeHtml(channel.name)}" ${disabled(Boolean(query))}>↑</button>
    <button class="icon" data-action="down" data-id="${id}" aria-label="Descendre ${escapeHtml(channel.name)}" ${disabled(Boolean(query))}>↓</button></td></tr>`;
}
function table(value: Codeplug): string {
  const visible = visibleChannels(value);
  return `<div class="table-panel"><div class="table-scroll"><table aria-label="Canaux analogiques"><thead><tr>
    <th><input type="checkbox" id="select-visible" aria-label="Sélectionner les canaux affichés" ${checked(visible.length > 0 && visible.every(channel => selected.has(channel.id)))}></th>
    <th>N°</th><th>Nom du canal</th><th>RX · MHz</th><th>TX · MHz</th><th>CTCSS RX / TX · Hz</th><th>FM</th><th>Puissance</th><th>Émission</th><th>Ordre</th>
    </tr></thead><tbody>${visible.length ? visible.map(channelRow).join('') : `<tr><td colspan="10"><div class="empty"><strong>${query ? 'Aucun résultat' : activeZone ? 'Cette zone est vide' : 'Votre prochaine fréquence commence ici.'}</strong><p>${query ? 'Essayez un autre nom ou une autre fréquence.' : activeZone ? 'Ajoutez des canaux existants avec « Membres ».' : 'Créez votre premier canal ou importez un codeplug.'}</p><button data-action="${activeZone ? 'members' : 'new-channel'}" class="primary">${activeZone ? 'Choisir les membres' : '＋ Créer un canal'}</button>${!activeZone ? ' <button data-action="example">Charger un exemple</button>' : ''}</div></td></tr>`}</tbody></table></div>
    <div class="table-footer"><span>${visible.length} affiché(s) · ${selected.size} sélectionné(s)</span><span>Fréquences en MHz · mode analogique FM</span></div></div>`;
}
function render(): void {
  const value = history.value;
  if (activeZone && !value.zones.some(zone => zone.id === activeZone)) activeZone = null;
  selected = new Set([...selected].filter(id => value.channels.some(channel => channel.id === id)));
  const zone = value.zones.find(item => item.id === activeZone);
  root.innerHTML = `<header><div class="brand"><div class="mark" aria-hidden="true">D578</div><div><strong>OpenD578</strong><small>Channel programming software</small></div></div><div class="header-right"><span>Éditeur de codeplug · v0.3</span><span class="badge">● Éditeur local · aucune écriture radio</span></div></header>
    <div class="workspace">${sidebar(value)}<main>
    <div class="page-heading"><div><p class="eyebrow">Codeplug / ${zone ? 'Zones' : 'Mémoires analogiques'}</p><h1>${escapeHtml(zone?.name ?? 'Tous les canaux')}</h1><p class="subtitle">Préparez vos mémoires, à votre rythme.</p></div>
    <div class="actions"><button data-action="bench">Banc émulé</button><button data-action="import">Importer</button><button data-action="csv">Exporter CSV</button><button data-action="export" class="primary">↓ Sauvegarder JSON</button></div></div>
    <div class="document-bar"><label for="document-name">Document</label><input id="document-name" value="${escapeHtml(value.name)}"><button class="icon" data-action="new">Nouveau</button><button class="icon" data-action="undo" ${disabled(!history.canUndo)} aria-label="Annuler la dernière modification">↶ Annuler</button><button class="icon" data-action="redo" ${disabled(!history.canRedo)} aria-label="Rétablir la modification">↷ Rétablir</button><span class="save-state">${storageProblem ? '⚠ Sauvegarde locale indisponible : exportez un JSON' : dirty() ? 'Session conservée sur ce navigateur · JSON à sauvegarder' : 'JSON à jour · session conservée sur ce navigateur'}</span></div>
    ${notice ? `<div class="notice ${isError ? 'error' : ''}" role="${isError ? 'alert' : 'status'}">${escapeHtml(notice)}</div>` : ''}
    <div class="toolbar"><input type="search" id="search" class="search" aria-label="Rechercher un canal" placeholder="Rechercher un nom, une fréquence…" value="${escapeHtml(query)}">
    <div class="actions">${zone ? '<button data-action="members">Membres</button><button data-action="rename-zone">Renommer</button><button data-action="delete-zone" class="danger">Supprimer la zone</button>' : ''}<button data-action="duplicate" ${disabled(!selected.size)}>Dupliquer</button><button data-action="bulk" ${disabled(!selected.size)}>Modifier la sélection</button><button data-action="delete" class="danger" ${disabled(!selected.size)}>Supprimer</button><button data-action="new-channel" class="primary">＋ Canal</button></div></div>
    ${table(value)}<p class="bottom-note">Format OpenD578 v1 · Les limites du poste seront vérifiées lors de sa connexion. Le CSV contient les canaux ; le JSON conserve aussi les zones et le VFO.</p></main></div>`;
  const selectAll = root.querySelector<HTMLInputElement>('#select-visible');
  const visible = visibleChannels(value);
  if (selectAll) selectAll.indeterminate = visible.some(channel => selected.has(channel.id)) && !visible.every(channel => selected.has(channel.id));
}

function openDialog(title: string, body: string, submit: (data: FormData) => void, label = 'Enregistrer'): void {
  dialog.innerHTML = `<form id="dialog-form"><div class="dialog-head"><h2 id="dialog-title">${escapeHtml(title)}</h2><button type="button" data-close aria-label="Fermer">×</button></div><div class="dialog-body"><div id="form-error" class="notice error" role="alert" hidden></div>${body}</div><div class="dialog-footer"><button type="button" data-close>Annuler</button><button type="submit" class="primary">${escapeHtml(label)}</button></div></form>`;
  dialog.querySelectorAll('[data-close]').forEach(button => button.addEventListener('click', () => dialog.close()));
  dialog.querySelector('form')!.addEventListener('submit', event => {
    event.preventDefault();
    try { submit(new FormData(event.currentTarget as HTMLFormElement)); dialog.close(); }
    catch (error) { const box = dialog.querySelector<HTMLDivElement>('#form-error')!; box.hidden = false; box.textContent = (error as Error).message; }
  });
  dialog.showModal();
}
function inputField(label: string, name: string, value: string, extra = ''): string {
  return `<label class="field">${label}<input name="${name}" value="${escapeHtml(value)}" ${extra}></label>`;
}
function settingsForm(value: AnalogSettings): string {
  return `${inputField('Réception · MHz', 'rx', formatMHz(value.rxHz), 'required inputmode="decimal"')}
    ${inputField('Émission · MHz', 'tx', formatMHz(value.txHz), 'required inputmode="decimal"')}
    <label class="field">Largeur FM<select name="bandwidth"><option value="narrow" ${value.bandwidth === 'narrow' ? 'selected' : ''}>Étroite</option><option value="wide" ${value.bandwidth === 'wide' ? 'selected' : ''}>Large</option></select></label>
    ${inputField('Niveau de puissance', 'power', value.power, 'required list="powers"')}<datalist id="powers"><option value="low"><option value="medium"><option value="high"></datalist>
    ${inputField('CTCSS RX · Hz', 'rxTone', value.rxCtcssDeciHz === null ? '' : toneText(value.rxCtcssDeciHz), 'inputmode="decimal" placeholder="Désactivé"')}
    ${inputField('CTCSS TX · Hz', 'txTone', value.txCtcssDeciHz === null ? '' : toneText(value.txCtcssDeciHz), 'inputmode="decimal" placeholder="Désactivé"')}
    <label class="check-label full"><input type="checkbox" name="inhibit" ${checked(value.txInhibit)}>Réception seule · émission interdite</label>
    <p class="help full">Laissez un CTCSS vide pour le désactiver. Les niveaux de puissance et les largeurs seront comparés aux capacités réelles du firmware avant transfert.</p>`;
}
function readTone(value: string): number | null {
  if (!value.trim()) return null;
  if (!/^\d+(?:[.,]\d)?$/.test(value.trim())) throw new Error('CTCSS : indiquez une valeur en Hz avec au plus une décimale.');
  return Math.round(Number(value.replace(',', '.')) * 10);
}
function readSettings(data: FormData): AnalogSettings {
  return { mode: 'FM', rxHz: parseMHz(String(data.get('rx'))), txHz: parseMHz(String(data.get('tx'))),
    bandwidth: data.get('bandwidth') as AnalogSettings['bandwidth'], power: String(data.get('power')).trim(),
    rxCtcssDeciHz: readTone(String(data.get('rxTone'))), txCtcssDeciHz: readTone(String(data.get('txTone'))), txInhibit: data.has('inhibit') };
}
function editChannel(id?: string): void {
  const value = history.value;
  const channel = id ? value.channels.find(item => item.id === id)! : { ...defaults(), id: newId('ch'), name: 'Nouveau canal' };
  openDialog(id ? 'Modifier le canal' : 'Nouveau canal', `<div class="form-grid">${inputField('Nom du canal', 'name', channel.name, 'required autofocus class="full"')}${settingsForm(channel)}</div>`, data => {
    const updated = { ...channel, ...readSettings(data), name: String(data.get('name')).trim() };
    const current = history.value;
    const channels = id ? current.channels.map(item => item.id === id ? updated : item) : [...current.channels, updated];
    const zones = !id && activeZone ? current.zones.map(zone => zone.id === activeZone ? { ...zone, channelIds: [...zone.channelIds, updated.id] } : zone) : current.zones;
    commit({ ...current, channels, zones });
  });
}
function editVfo(): void {
  openDialog('Réglages du VFO', `<div class="form-grid"><label class="check-label full"><input type="checkbox" name="enabled" ${checked(history.value.vfo !== null)}>Inclure le VFO dans le codeplug</label>${settingsForm(history.value.vfo ?? defaults())}</div>`, data => {
    commit({ ...history.value, vfo: data.has('enabled') ? readSettings(data) : null });
  });
}
function editZone(rename = false): void {
  const zone = history.value.zones.find(item => item.id === activeZone);
  openDialog(rename ? 'Renommer la zone' : 'Nouvelle zone', inputField('Nom de la zone', 'name', rename ? zone!.name : 'Nouvelle zone', 'required autofocus'), data => {
    const name = String(data.get('name')).trim();
    const value = history.value;
    const nextZone: Zone = rename ? { ...zone!, name } : { id: newId('zone'), name, channelIds: [] };
    const next = { ...value, zones: rename ? value.zones.map(item => item.id === nextZone.id ? nextZone : item) : [...value.zones, nextZone] };
    history.commit(next); activeZone = nextZone.id; persist(); render();
  });
}
function editMembers(): void {
  const value = history.value, zone = value.zones.find(item => item.id === activeZone)!;
  openDialog('Canaux de la zone', `<p class="help">Cochez les canaux à inclure. Leur ordre existant est conservé ; utilisez les flèches du tableau pour le modifier.</p><div class="member-list">${value.channels.length ? value.channels.map(channel => `<label class="check-label"><input type="checkbox" name="members" value="${escapeHtml(channel.id)}" ${checked(zone.channelIds.includes(channel.id))}>${escapeHtml(channel.name)} <span class="freq">${formatMHz(channel.rxHz)}</span></label>`).join('') : '<p>Créez d’abord un canal.</p>'}</div>`, data => {
    const ids = data.getAll('members').map(String);
    const channelIds = [...zone.channelIds.filter(id => ids.includes(id)), ...ids.filter(id => !zone.channelIds.includes(id))];
    commit({ ...history.value, zones: history.value.zones.map(item => item.id === zone.id ? { ...item, channelIds } : item) });
  });
}
function bulkEdit(): void {
  openDialog(`Modifier ${selected.size} canal(aux)`, `<div class="form-grid"><label class="field">Largeur FM<select name="bandwidth"><option value="">Conserver</option><option value="narrow">Étroite</option><option value="wide">Large</option></select></label>${inputField('Puissance (vide : conserver)', 'power', '')}<label class="field full">Émission<select name="inhibit"><option value="">Conserver</option><option value="true">Réception seule</option><option value="false">Autoriser RX / TX</option></select></label></div>`, data => {
    const channels = history.value.channels.map(channel => !selected.has(channel.id) ? channel : {
      ...channel, bandwidth: (data.get('bandwidth') || channel.bandwidth) as Channel['bandwidth'],
      power: String(data.get('power')).trim() || channel.power,
      txInhibit: data.get('inhibit') === '' ? channel.txInhibit : data.get('inhibit') === 'true',
    });
    commit({ ...history.value, channels });
  });
}
function duplicateSelected(): void {
  const value = history.value;
  const copies = value.channels.filter(channel => selected.has(channel.id)).map(channel => ({ ...channel, id: newId('ch'), name: `${channel.name} copie` }));
  const zones = activeZone ? value.zones.map(zone => zone.id === activeZone ? { ...zone, channelIds: [...zone.channelIds, ...copies.map(channel => channel.id)] } : zone) : value.zones;
  commit({ ...value, channels: [...value.channels, ...copies], zones });
  selected = new Set(copies.map(channel => channel.id)); render();
}
function moveChannel(id: string, delta: -1 | 1): void {
  const value = history.value;
  if (activeZone) {
    commit({ ...value, zones: value.zones.map(zone => zone.id !== activeZone ? zone : { ...zone, channelIds: moveItem(zone.channelIds, zone.channelIds.indexOf(id), delta) }) });
  } else commit({ ...value, channels: moveItem(value.channels, value.channels.findIndex(channel => channel.id === id), delta) });
}
function download(text: string, extension: string, mime: string): void {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  const anchor = document.createElement('a'); anchor.href = url;
  anchor.download = `${history.value.name.replace(/[<>:"/\\|?*]/g, '_')}.${extension}`;
  document.body.append(anchor); anchor.click(); anchor.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function exportJson(): void {
  const source = serializeCodeplug(history.value); download(source, 'opend578.json', 'application/json');
  exportedSnapshot = source; persist(); notice = 'Export JSON demandé. Vérifiez le fichier dans vos téléchargements.'; isError = false; render();
}
function replaceDocument(value: Codeplug, message: string): void {
  if (dirty() && !confirm('Remplacer le document actuel ? Vous pourrez annuler cette action.')) return;
  history.commit(value); activeZone = null; selected.clear(); query = ''; persist(); notice = message; isError = false; render();
}
async function importFile(file: File): Promise<void> {
  if (file.size > 10 * 1024 * 1024) throw new Error('Fichier trop volumineux : maximum 10 Mio pour cet éditeur.');
  const text = await file.text();
  if (file.name.toLowerCase().endsWith('.csv')) {
    const channels = parseChannelsCsv(text);
    const next = appendChannels(history.value, channels);
    if (!confirm(`Ajouter ${channels.length} canal(aux) au document ? Le CSV ne modifie ni les zones ni le VFO.`)) return;
    commit(next, `${channels.length} canal(aux) importé(s).`);
  } else replaceDocument(parseCodeplug(text), 'Codeplug JSON importé.');
}

root.addEventListener('click', async event => {
  const button = (event.target as HTMLElement).closest<HTMLButtonElement>('button[data-action]');
  if (!button || button.disabled) return;
  const action = button.dataset.action, id = button.dataset.id!;
  try {
    switch (action) {
      case 'bench': openBenchPanel(); break;
      case 'all': activeZone = null; selected.clear(); render(); break;
      case 'zone': activeZone = id; selected.clear(); render(); break;
      case 'new-channel': editChannel(); break;
      case 'edit': editChannel(id); break;
      case 'vfo': editVfo(); break;
      case 'new-zone': editZone(); break;
      case 'rename-zone': editZone(true); break;
      case 'members': editMembers(); break;
      case 'delete-zone': if (confirm('Supprimer cette zone ? Ses canaux seront conservés.')) commit({ ...history.value, zones: history.value.zones.filter(zone => zone.id !== activeZone) }); break;
      case 'delete': if (confirm(`Supprimer ${selected.size} canal(aux), y compris leurs références dans les zones ?`)) commit(deleteChannels(history.value, [...selected])); break;
      case 'duplicate': duplicateSelected(); break;
      case 'bulk': bulkEdit(); break;
      case 'up': moveChannel(id, -1); break;
      case 'down': moveChannel(id, 1); break;
      case 'undo': history.undo(); persist(); notice = 'Modification annulée.'; isError = false; render(); break;
      case 'redo': history.redo(); persist(); notice = 'Modification rétablie.'; isError = false; render(); break;
      case 'new': replaceDocument(createCodeplug(), 'Nouveau document.'); break;
      case 'export': exportJson(); break;
      case 'csv': download(serializeChannelsCsv(history.value.channels), 'csv', 'text/csv;charset=utf-8'); break;
      case 'import': fileInput.value = ''; fileInput.click(); break;
      case 'example': {
        const response = await fetch('./examples/analog.opend578.json');
        if (!response.ok) throw new Error('Exemple indisponible.');
        replaceDocument(parseCodeplug(await response.text()), 'Exemple synthétique chargé : aucun relais local réel.'); break;
      }
    }
  } catch (error) { fail(error); }
});
root.addEventListener('input', event => {
  const input = event.target as HTMLInputElement;
  if (input.id !== 'search') return;
  const position = input.selectionStart; query = input.value; render();
  const next = root.querySelector<HTMLInputElement>('#search')!; next.focus();
  if (position !== null) { try { next.setSelectionRange(position, position); } catch { /* search inputs may not expose selection */ } }
});
root.addEventListener('change', event => {
  const input = event.target as HTMLInputElement;
  try {
    if (input.id === 'document-name') commit({ ...history.value, name: input.value.trim() });
    if (input.dataset.select) { input.checked ? selected.add(input.dataset.select) : selected.delete(input.dataset.select); render(); }
    if (input.id === 'select-visible') {
      for (const channel of visibleChannels(history.value)) input.checked ? selected.add(channel.id) : selected.delete(channel.id);
      render();
    }
  } catch (error) { fail(error); }
});
fileInput.addEventListener('change', () => { const file = fileInput.files?.[0]; if (file) importFile(file).catch(fail); });
window.addEventListener('beforeunload', event => { if (dirty() || dialog.open) { event.preventDefault(); event.returnValue = ''; } });
window.addEventListener('keydown', event => {
  if (!(event.ctrlKey || event.metaKey) || dialog.open || document.querySelector<HTMLDialogElement>('#bench-dialog')!.open) return;
  if (event.key.toLowerCase() === 's') { event.preventDefault(); exportJson(); return; }
  if ((event.target as HTMLElement).matches('input,select,textarea,[contenteditable]')) return;
  if (event.key.toLowerCase() === 'z') { event.preventDefault(); event.shiftKey ? history.redo() : history.undo(); persist(); render(); }
});
render();
