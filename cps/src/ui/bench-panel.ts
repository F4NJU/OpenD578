import { formatOemTone } from '../device/oem-profile.ts';
import { BenchHttpApi, benchOrigin } from '../device/bench-http.ts';
import { OemReadOnlyClient } from '../device/oem-readonly.ts';
import type { OemSnapshot } from '../device/oem-readonly.ts';
import { formatMHz } from '../core/frequency.ts';
import { appendOemSlots, oemImportReason, mergeOemSnapshots } from '../core/oem-import.ts';
import type { Codeplug } from '../core/model.ts';
import { powerField, readPower, bindChannelFields } from './channel-fields.ts';

const benchDialog = document.querySelector<HTMLDialogElement>('#bench-dialog')!;
const SPENT_ENGINE_KEY = 'opend578.cps.oem.spent-engine.v1';
let benchBusy = false;
let benchAbort: AbortController | null = null;
let oemSnapshot: OemSnapshot | null = null;
let oemClient: OemReadOnlyClient | null = null;
let oemSelected = new Set<number>();
let oemSpentEngine: string | null = null;
let benchGetDocument: (() => Codeplug) | null = null;
let benchCommitDocument: ((next: Codeplug) => void) | null = null;
const benchEscape = (value: unknown): string => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]!);

function isBenchPage(): boolean {
  try { return location.pathname.startsWith('/cps/') && benchOrigin(location.origin) === location.origin; }
  catch { return false; }
}
function spentEngine(): string | null {
  if (oemSpentEngine) return oemSpentEngine;
  try { return sessionStorage.getItem(SPENT_ENGINE_KEY); } catch { return null; }
}
function benchMessage(text: string, error = false): void {
  const status = benchDialog.querySelector<HTMLDivElement>('#bench-status')!;
  status.textContent = text; status.classList.toggle('error', error);
  status.setAttribute('role', error ? 'alert' : 'status');
}
function renderOemSnapshot(): void {
  const target = benchDialog.querySelector<HTMLDivElement>('#bench-results')!;
  if (!oemSnapshot) { target.replaceChildren(); return; }
  const snapshot = oemSnapshot;
  oemSelected = new Set([...oemSelected].filter(number => snapshot.slots.some(slot => slot.slot === number && !oemImportReason(slot))));
  target.innerHTML = `<p class="help">Instantané du ${benchEscape(new Date(snapshot.readAt).toLocaleString('fr-FR'))} · modèle déclaré : ${snapshot.model} · version non décodée · moteur ${benchEscape(snapshot.engine)}. ${snapshot.endAcknowledged ? "END acquitté." : "Session ouverte : vous pouvez continuer à lire."}</p>
    <div class="table-scroll"><table aria-label="Emplacements OEM en lecture seule"><thead><tr><th>Slot</th><th>Nom</th><th>RX · MHz</th><th>TX · MHz</th><th>CTCSS/DCS RX</th><th>CTCSS/DCS TX</th><th>Mode · bits OEM</th><th>Puissance · bits OEM</th></tr></thead><tbody>${snapshot.slots.map(slot => `<tr><td>${slot.slot}</td><td>${benchEscape(slot.name ?? 'Nom non interprétable')}</td><td class="freq">${slot.rxHz === null ? 'Inconnue' : formatMHz(slot.rxHz)}</td><td class="freq">${slot.txHz === null ? 'Inconnue' : formatMHz(slot.txHz)}</td><td>${benchEscape(formatOemTone(slot.rxTone))}</td><td>${benchEscape(formatOemTone(slot.txTone))}</td><td>${benchEscape(slot.mode)}</td><td>${benchEscape(slot.power)}</td></tr>`).join('')}</tbody></table></div>
    <p class="help">${snapshot.slots.length} emplacements ${snapshot.scope === "active-channels" ? "actifs selon le bitmap OEM (capacité 4000)" : "lus et cumulés"}. Tonalités RX/TX décodées selon le profil V1.21. Les DCS et tonalités inconnues ne sont pas importés.</p>
    <p class="help">${snapshot.endAcknowledged ? "Session terminée : préparation possible." : "Cliquez sur Terminer la session avant de préparer un import. Vous pouvez encore relire ou changer de groupe."}</p><form id="bench-import-form"><fieldset><h3>Préparer des canaux FM dans le document</h3>
    <p class="help">Sélectionnez les emplacements voulus. Leur nom et leurs fréquences seront copiés. Les modes mixtes/DMR et les valeurs inconnues sont exclus. Aucun transfert vers le poste n'est effectué.</p>
    <button type="button" id="bench-select-fm">Sélectionner les FM interprétables</button>
    <div>${snapshot.slots.map(slot => { const reason = oemImportReason(slot); return `<label><input type="checkbox" name="oem-slot" value="${slot.slot}" ${oemSelected.has(slot.slot) ? "checked" : ""} ${reason ? 'disabled' : ''}> ${slot.slot} · ${benchEscape(slot.name ?? 'Sans nom')} ${reason ? `— ${benchEscape(reason)}` : ''}</label><br>`; }).join('')}</div>
    <label class="field">Largeur à utiliser — non lue dans le poste<select name="bandwidth" required><option value="">Choisir</option><option value="narrow">Étroite</option><option value="wide">Large</option></select></label>
    ${powerField('low')}
    <p class="help">La puissance choisie ci-dessus est un identifiant du document PC, indépendant des bits OEM affichés. Les CTCSS RX et TX lus sont conservés ; « aucune » reste sans tonalité. L'émission sera désactivée pour tous les canaux ajoutés ; vérifiez ces réglages avant de la réactiver. Zones, scans et VFO restent conservés.</p>
    <label><input type="checkbox" name="reviewed" required> J'ai vérifié la sélection et ces réglages de préparation.</label>
    <button type="submit" class="primary" ${snapshot.endAcknowledged ? "" : "disabled"}>Ajouter la sélection en réception seule</button></fieldset></form>`;
  const form = target.querySelector<HTMLFormElement>('#bench-import-form')!;
  bindChannelFields(form);
  form.querySelector('#bench-select-fm')!.addEventListener('click', () => {
    form.querySelectorAll<HTMLInputElement>('input[name="oem-slot"]:not(:disabled)').forEach(input => { input.checked = true; oemSelected.add(Number(input.value)); });
  });
  form.addEventListener('change', () => { form.querySelectorAll<HTMLInputElement>('input[name="oem-slot"]:not(:disabled)').forEach(input => { if (input.checked) oemSelected.add(Number(input.value)); else oemSelected.delete(Number(input.value)); }); });
  form.addEventListener('submit', event => {
    event.preventDefault();
    if (!snapshot.endAcknowledged || benchBusy || !form.reportValidity() || !benchGetDocument || !benchCommitDocument) return;
    try {
      const data = new FormData(form);
      const next = appendOemSlots(benchGetDocument(), snapshot, data.getAll('oem-slot').map(Number), {
        bandwidth: String(data.get('bandwidth')) as 'narrow' | 'wide', power: readPower(data),
      });
      benchCommitDocument(next); benchDialog.close();
    } catch (error) { benchMessage((error as Error).message, true); }
  });
}
function benchControls(busy: boolean): void {
  benchDialog.querySelectorAll<HTMLButtonElement | HTMLSelectElement>('#bench-read, #bench-all, #bench-page, #bench-export').forEach(control => { control.disabled = busy || (control.id === 'bench-export' && !oemSnapshot); });
  benchDialog.querySelector<HTMLButtonElement>('#bench-cancel')!.disabled = !busy;
  benchDialog.querySelector<HTMLButtonElement>('#bench-end')!.disabled = busy || !oemClient?.sessionOpen;
  benchDialog.querySelectorAll<HTMLButtonElement>('[data-bench-close]').forEach(button => { button.disabled = busy || Boolean(oemClient?.sessionOpen); });
}
async function readBenchPage(all = false): Promise<void> {
  if (benchBusy) return;
  const page = Number(benchDialog.querySelector<HTMLSelectElement>('#bench-page')!.value);
  const previous = oemClient?.sessionOpen ? oemSnapshot : null;
  if (!previous) oemSelected.clear();
  oemSnapshot = null; renderOemSnapshot();
  benchBusy = true; benchAbort ??= new AbortController(); benchControls(true);
  const progress = benchDialog.querySelector<HTMLProgressElement>('#bench-progress')!;
  progress.value = 0;
  benchMessage('Connexion à l’API du banc, identification et lecture…');
  try {
    if (!oemClient) {
      const api = new BenchHttpApi({ signal: benchAbort.signal });
      await api.initialize();
      oemClient = new OemReadOnlyClient((path, data) => api.request(path, data), {
        signal: benchAbort.signal, spentEngine: spentEngine(),
        markEngine: engine => { oemSpentEngine = engine; try { if (engine === null) sessionStorage.removeItem(SPENT_ENGINE_KEY); else sessionStorage.setItem(SPENT_ENGINE_KEY, engine); } catch { /* Keep the in-memory guard when storage is unavailable. */ } },
        progress: (done, total) => { progress.value = done / total; benchMessage(`D578UV identifié · lecture ${Math.round(100 * done / total)} %`); },
      });
    }
    const snapshot = all ? await oemClient.readAll() : await oemClient.readPage(page, { keepSession: true });
    oemSnapshot = mergeOemSnapshots(previous, snapshot); renderOemSnapshot();
    benchMessage(all ? "Lecture globale terminée et END acquitté. Sélectionnez les canaux à importer. Un redémarrage du moteur sera nécessaire pour une nouvelle session." : "Lecture terminée. La session reste ouverte : relisez ce groupe ou choisissez le suivant. Terminer la session envoie END une seule fois.");
  } catch (error) {
    const aborted = benchAbort.signal.aborted; oemClient = null; benchAbort = null;
    benchMessage(aborted ? 'Lecture interrompue localement. Une commande déjà envoyée peut encore être traitée : redémarrez le moteur du banc avant de reprendre.' : `${(error as Error).message}\nAprès une session engagée, redémarrez le moteur du banc avant de reprendre. Aucun nouvel instantané n’est validé.`, true);
  } finally { benchBusy = false; benchControls(false); }
}
async function finishBenchSession(): Promise<void> {
  if (benchBusy || !oemClient?.sessionOpen) return;
  benchBusy = true; benchControls(true);
  try {
    await oemClient.endSession();
    if (oemSnapshot) oemSnapshot = { ...oemSnapshot, endAcknowledged: true };
    renderOemSnapshot();
    benchMessage('Session terminée, END acquitté. Vous pouvez préparer un import. Le firmware demande ensuite son redémarrage : pour une nouvelle session, redémarrez le moteur du banc.');
  } catch (error) {
    oemSnapshot = null; renderOemSnapshot(); benchMessage((error as Error).message + ' Redémarrez le moteur avant de reprendre.', true);
  } finally { oemClient = null; benchAbort = null; benchBusy = false; benchControls(false); }
}
function exportOemSnapshot(): void {
  if (!oemSnapshot) return;
  const source = JSON.stringify({ format: 'opend578-oem-readonly-v1', ...oemSnapshot }, null, 2);
  const url = URL.createObjectURL(new Blob([source], { type: 'application/json' }));
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = oemSnapshot.page === -1 ? 'OpenD578-OEM-canaux.json' : `OpenD578-OEM-slots-${oemSnapshot.page * 32 + 1}-${oemSnapshot.page * 32 + 32}.json`;
  document.body.append(anchor); anchor.click(); anchor.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function openBenchPanel(getDocument: () => Codeplug, commitDocument: (next: Codeplug) => void): void {
  benchGetDocument = getDocument; benchCommitDocument = commitDocument;
  const sameOrigin = isBenchPage();
  benchDialog.innerHTML = `<div class="dialog-head"><h2 id="bench-title">Banc émulé · lecture OEM</h2><button data-bench-close aria-label="Fermer">×</button></div>
    <div class="dialog-body"><p class="help">Adaptateur de recherche D578UV, profil OEM V1.21. Ce panneau utilise uniquement le protocole constructeur. Pour l’alpha avec extension CPS, ouvrir OpenD578 · VFO. Fermez le CPS intégré et tout pont externe : un seul client USB à la fois.</p>
    ${sameOrigin ? `<div class="toolbar"><label class="field">Groupe d’emplacements<select id="bench-page"><option value="0">1–32</option><option value="1">33–64</option><option value="2">65–96</option><option value="3">97–128</option></select></label><div class="actions"><button id="bench-all" class="primary">Lire tous les canaux actifs</button><button id="bench-read">Lire ce groupe</button><button id="bench-end" disabled>Terminer la session</button><button id="bench-cancel" disabled>Interrompre</button><button id="bench-export" disabled>Exporter l’instantané</button></div></div><progress id="bench-progress" max="1" value="0" aria-label="Progression de lecture"></progress><div id="bench-status" class="notice" role="status">Démarrez le firmware OEM dans le banc avant de lire. Aucune commande d’écriture de codeplug n’est envoyée. PROGRAM et END ouvrent et ferment la session de programmation.</div><div id="bench-results"></div>` : `<p>Pour conserver la protection du banc, le CPS connecté doit être ouvert depuis sa propre adresse.</p><form id="bench-open-form"><label class="field">Adresse locale affichée par le banc Python<input id="bench-url" type="url" value="http://127.0.0.1:8765" required></label><p class="help">Le banc doit être mis à jour avec cette branche et le CPS compilé (npm run build). Le simulateur GitHub Pages n’expose pas cette API HTTP.</p><p class="help">Le nouvel onglet utilise une session de navigateur distincte de celle de ce fichier HTML. Exportez votre JSON si vous souhaitez le déplacer ; la lecture OEM reste une inspection séparée.</p><div id="bench-status" class="notice" role="status">Aucune connexion n’est faite depuis ce fichier.</div><button class="primary" type="submit">Ouvrir le CPS dans le banc</button></form>`}
    </div><div class="dialog-footer"><button data-bench-close>Fermer</button></div>`;
  benchDialog.querySelectorAll('[data-bench-close]').forEach(button => button.addEventListener('click', () => benchDialog.close()));
  if (sameOrigin) {
    benchDialog.querySelector('#bench-all')!.addEventListener('click', () => { void readBenchPage(true); });
    benchDialog.querySelector('#bench-read')!.addEventListener('click', () => { void readBenchPage(); });
    benchDialog.querySelector('#bench-end')!.addEventListener('click', () => { void finishBenchSession(); });
    benchDialog.querySelector('#bench-cancel')!.addEventListener('click', () => benchAbort?.abort(new Error('Lecture annulée')));
    benchDialog.querySelector('#bench-export')!.addEventListener('click', exportOemSnapshot);
    renderOemSnapshot(); benchControls(false);
  } else {
    benchDialog.querySelector('#bench-open-form')!.addEventListener('submit', event => {
      event.preventDefault();
      try {
        const origin = benchOrigin(benchDialog.querySelector<HTMLInputElement>('#bench-url')!.value);
        window.open(`${origin}/cps/`, '_blank', 'noopener,noreferrer');
        benchMessage('Ouverture demandée. Dans le nouvel onglet, cliquez sur « Banc émulé », puis « Identifier et lire ».');
      } catch (error) { benchMessage((error as Error).message, true); }
    });
  }
  benchDialog.showModal();
}
benchDialog.addEventListener('cancel', event => { if (oemClient?.sessionOpen && !benchBusy) { event.preventDefault(); benchMessage('Terminez la session avant de fermer ce panneau.'); return; } if (benchBusy) { event.preventDefault(); benchAbort?.abort(new Error('Lecture annulée')); } });
window.addEventListener('beforeunload', event => { if (benchBusy || oemClient?.sessionOpen) { event.preventDefault(); event.returnValue = ''; } });
