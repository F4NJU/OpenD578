import type { Codeplug } from '../core/model.ts';
import { CSV_FIELDS, readCsvTable, suggestCsvMapping, previewCsvImport, applyCsvImport } from '../core/csv-mapping.ts';
import type { CsvField, CsvTable, CsvPreviewRow, CsvImportOptions } from '../core/csv-mapping.ts';
import { formatMHz } from '../core/frequency.ts';

const csvDialog = document.querySelector<HTMLDialogElement>('#csv-import-dialog')!;
const csvEscape = (value: unknown): string => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]!);
const CSV_LABELS: Record<CsvField, string> = { name: 'Nom *', rx: 'Fréquence RX *', tx: 'Fréquence TX', offset: 'Valeur du décalage', direction: 'Sens du décalage', rxTone: 'CTCSS RX · Hz', txTone: 'CTCSS TX · Hz', power: 'Puissance', bandwidth: 'Largeur FM', mode: 'Mode', inhibit: 'RX seul / TX interdit' };

export function openCsvImport(source: string, getValue: () => Codeplug, save: (value: Codeplug) => void): void {
  let table: CsvTable | null = null, preview: CsvPreviewRow[] = [], selected = new Set<number>(), page = 0, delimiter = 'auto';
  let options: CsvImportOptions = { mapping: {} as CsvImportOptions['mapping'], frequencyUnit: 'MHz', offsetUnit: 'MHz', offsetDirection: 'minus', power: 'low', bandwidth: 'narrow', txInhibit: true };
  let parseError = '';
  function loadTable(): void {
    try { table = readCsvTable(source, delimiter === 'auto' ? undefined : delimiter as ',' | ';' | '\t'); options.mapping = suggestCsvMapping(table.headers); parseError = ''; }
    catch (error) { table = null; parseError = (error as Error).message; }
    preview = []; selected.clear(); page = 0; renderConfig();
  }
  function showError(error: unknown): void {
    const box = csvDialog.querySelector<HTMLDivElement>('#csv-error')!;
    box.hidden = false; box.textContent = (error as Error).message;
  }
  function renderConfig(): void {
    const value = getValue();
    csvDialog.innerHTML = `<div class="dialog-head"><h2 id="csv-import-title">Importer un CSV externe</h2><button type="button" data-csv="close" aria-label="Fermer">×</button></div><div class="dialog-body"><p class="help">CSV UTF-8 avec en-tête. Vérifiez les suggestions : aucun format de CPS tiers n’est certifié. Les identifiants source sont ignorés ; chaque canal ajouté reçoit un nouvel identifiant.</p><div id="csv-error" class="notice error" role="alert" ${parseError ? '' : 'hidden'}>${csvEscape(parseError)}</div>
      <form id="csv-map-form"><div class="form-grid"><label class="field">Séparateur<select id="csv-separator">${[['auto', 'Automatique'], [',', 'Virgule'], [';', 'Point-virgule'], ['\t', 'Tabulation']].map(([id, label]) => `<option value="${id}" ${delimiter === id ? 'selected' : ''}>${label}</option>`).join('')}</select></label>
      ${table ? CSV_FIELDS.map(field => `<label class="field">${CSV_LABELS[field]}<select name="map-${field}"><option value="">Non associé</option>${table!.headers.map((header, index) => `<option value="${index}" ${options.mapping[field] === index ? 'selected' : ''}>${index + 1}. ${csvEscape(header || '(sans nom)')}</option>`).join('')}</select></label>`).join('') : ''}</div>
      <h3>Unités et valeurs par défaut</h3><div class="form-grid"><label class="field">Unité RX / TX<select name="unit">${['MHz', 'kHz', 'Hz'].map(unit => `<option ${options.frequencyUnit === unit ? 'selected' : ''}>${unit}</option>`).join('')}</select></label><label class="field">Unité du décalage<select name="offset-unit">${['MHz', 'kHz', 'Hz'].map(unit => `<option ${options.offsetUnit === unit ? 'selected' : ''}>${unit}</option>`).join('')}</select></label><label class="field">Sens si décalage non signé<select name="offset-direction"><option value="minus" ${options.offsetDirection === 'minus' ? 'selected' : ''}>− Négatif</option><option value="plus" ${options.offsetDirection === 'plus' ? 'selected' : ''}>+ Positif</option></select></label><label class="field">Puissance par défaut<input name="power" value="${csvEscape(options.power)}" required></label><label class="field">Largeur par défaut<select name="bandwidth"><option value="narrow" ${options.bandwidth === 'narrow' ? 'selected' : ''}>Étroite</option><option value="wide" ${options.bandwidth === 'wide' ? 'selected' : ''}>Large</option></select></label><label class="check-label"><input type="checkbox" name="inhibit" ${options.txInhibit ? 'checked' : ''}>RX seul par défaut</label></div>
      <p class="help">Les valeurs par défaut s’appliquent aux colonnes absentes ou cellules vides. Sans TX ni décalage, TX = RX. Le signe du décalage est conservé ; un conflit avec TX est refusé. CTCSS en Hz, DCS non pris en charge. Les niveaux de puissance sont des identifiants, pas des watts.</p><p><button type="submit" class="primary" ${table ? '' : 'disabled'}>Prévisualiser</button></p></form>
      <div id="csv-preview"></div><div class="toolbar"><label class="field">Zone de destination<select id="csv-zone"><option value="">Aucune · liste globale</option>${value.zones.map(zone => `<option value="${csvEscape(zone.id)}">${csvEscape(zone.name)}</option>`).join('')}</select></label><button type="button" id="csv-apply" data-csv="apply" class="primary" disabled>Importer la sélection</button></div></div>`;
    csvDialog.querySelector('#csv-map-form')!.addEventListener('submit', event => { event.preventDefault(); runPreview(); });
    csvDialog.querySelector('#csv-map-form')!.addEventListener('change', event => {
      if ((event.target as HTMLElement).id === 'csv-separator') { delimiter = (event.target as HTMLSelectElement).value; loadTable(); return; }
      invalidate();
    });
    csvDialog.querySelector('#csv-map-form')!.addEventListener('input', event => { if ((event.target as HTMLElement).tagName === 'INPUT') invalidate(); });
  }
  function invalidate(): void {
    preview = []; selected.clear(); csvDialog.querySelector('#csv-preview')!.textContent = 'Options modifiées : cliquez sur Prévisualiser pour recalculer.';
    csvDialog.querySelector<HTMLButtonElement>('#csv-apply')!.disabled = true;
  }
  function runPreview(): void {
    if (!table) return;
    const form = new FormData(csvDialog.querySelector<HTMLFormElement>('#csv-map-form')!);
    options = { mapping: Object.fromEntries(CSV_FIELDS.map(field => [field, form.get(`map-${field}`) === '' ? null : Number(form.get(`map-${field}`))])) as CsvImportOptions['mapping'],
      frequencyUnit: form.get('unit') as CsvImportOptions['frequencyUnit'], offsetUnit: form.get('offset-unit') as CsvImportOptions['offsetUnit'],
      offsetDirection: form.get('offset-direction') as CsvImportOptions['offsetDirection'], power: String(form.get('power')).trim(),
      bandwidth: form.get('bandwidth') as CsvImportOptions['bandwidth'], txInhibit: form.has('inhibit') };
    try {
      preview = previewCsvImport(table, options, getValue()); page = 0;
      selected = new Set(preview.filter(row => row.channel && !row.duplicates.length).map(row => row.record));
      csvDialog.querySelector<HTMLDivElement>('#csv-error')!.hidden = true; renderPreview();
    } catch (error) { invalidate(); showError(error); }
  }
  function renderPreview(): void {
    const rows = preview.slice(page * 50, (page + 1) * 50), valid = preview.filter(row => row.channel).length, duplicates = preview.filter(row => row.duplicates.length).length;
    csvDialog.querySelector('#csv-preview')!.innerHTML = `<h3>Aperçu · ${preview.length} enregistrement(s)</h3><p role="status">${valid} valide(s) · ${preview.length - valid} invalide(s) · ${duplicates} doublon(s) présumé(s) · ${selected.size} sélectionné(s)</p><p class="help">Les doublons sont décochés par défaut, mais peuvent être inclus volontairement. La sélection porte sur toutes les pages.</p><div class="actions"><button type="button" data-csv="clean">Sélectionner les valides sans doublons</button><button type="button" data-csv="all">Toutes les valides, doublons inclus</button><button type="button" data-csv="none">Tout décocher</button></div>
      <div class="table-scroll"><table aria-label="Aperçu CSV"><thead><tr><th>Choix</th><th>Enreg.</th><th>Nom</th><th>RX · MHz</th><th>TX · MHz</th><th>CTCSS RX / TX</th><th>Puissance / FM</th><th>TX</th><th>État</th></tr></thead><tbody>${rows.map(row => `<tr><td><input type="checkbox" data-csv-row="${row.record}" aria-label="Importer l’enregistrement ${row.record}" ${row.channel ? '' : 'disabled'} ${selected.has(row.record) ? 'checked' : ''}></td><td>${row.record}</td><td>${csvEscape(row.channel?.name ?? '—')}</td><td class="freq">${row.channel ? formatMHz(row.channel.rxHz) : '—'}</td><td class="freq">${row.channel ? formatMHz(row.channel.txHz) : '—'}</td><td>${row.channel ? `${row.channel.rxCtcssDeciHz === null ? '—' : row.channel.rxCtcssDeciHz / 10} / ${row.channel.txCtcssDeciHz === null ? '—' : row.channel.txCtcssDeciHz / 10}` : '—'}</td><td>${row.channel ? csvEscape(`${row.channel.power} / ${row.channel.bandwidth}`) : '—'}</td><td>${row.channel ? row.channel.txInhibit ? 'RX seul' : 'RX/TX' : '—'}</td><td>${csvEscape([...row.errors, ...row.duplicates].join(' · ') || 'Valide')}</td></tr>`).join('')}</tbody></table></div><div class="toolbar"><button type="button" data-csv="prev" ${page === 0 ? 'disabled' : ''}>Précédent</button><span>Page ${page + 1} / ${Math.max(1, Math.ceil(preview.length / 50))} · 50 lignes par page</span><button type="button" data-csv="next" ${(page + 1) * 50 >= preview.length ? 'disabled' : ''}>Suivant</button></div>`;
    csvDialog.querySelector<HTMLButtonElement>('#csv-apply')!.disabled = !selected.size;
    csvDialog.querySelector<HTMLButtonElement>('#csv-apply')!.textContent = `Importer ${selected.size} canal(aux)`;
  }
  csvDialog.onclick = event => {
    const button = (event.target as HTMLElement).closest<HTMLButtonElement>('[data-csv]');
    if (!button || button.disabled) return;
    try {
      const action = button.dataset.csv;
      if (action === 'close') { csvDialog.close(); return; }
      if (action === 'apply') {
        const zoneId = csvDialog.querySelector<HTMLSelectElement>('#csv-zone')!.value || null;
        const records = preview.filter(row => selected.has(row.record)).map(row => row.record);
        if (!confirm(`Ajouter ${records.length} canal(aux) ? Les lignes cochées en doublon seront conservées. Une seule annulation retirera cet import.`)) return;
        save(applyCsvImport(getValue(), preview, records, zoneId, () => `ch-${crypto.randomUUID()}`)); csvDialog.close(); return;
      }
      if (action === 'clean' || action === 'all') selected = new Set(preview.filter(row => row.channel && (action === 'all' || !row.duplicates.length)).map(row => row.record));
      if (action === 'none') selected.clear();
      if (action === 'prev') page--;
      if (action === 'next') page++;
      renderPreview();
    } catch (error) { showError(error); }
  };
  csvDialog.onchange = event => {
    const input = event.target as HTMLInputElement;
    if (!input.dataset.csvRow) return;
    const record = Number(input.dataset.csvRow); input.checked ? selected.add(record) : selected.delete(record); renderPreview();
  };
  loadTable(); csvDialog.showModal();
}
window.addEventListener('beforeunload', event => { if (csvDialog.open) { event.preventDefault(); event.returnValue = ''; } });
