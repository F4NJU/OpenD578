import { BenchHttpApi, benchOrigin } from '../device/bench-http.ts';
import { OemReadOnlyClient } from '../device/oem-readonly.ts';
import type { OemSnapshot } from '../device/oem-readonly.ts';
import { formatMHz } from '../core/frequency.ts';

const benchDialog = document.querySelector<HTMLDialogElement>('#bench-dialog')!;
const SPENT_ENGINE_KEY = 'opend578.cps.oem.spent-engine.v1';
let benchBusy = false;
let benchAbort: AbortController | null = null;
let oemSnapshot: OemSnapshot | null = null;
let oemSpentEngine: string | null = null;
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
  target.innerHTML = `<p class="help">Instantané du ${benchEscape(new Date(snapshot.readAt).toLocaleString('fr-FR'))} · modèle déclaré : ${snapshot.model} · version non décodée · moteur ${benchEscape(snapshot.engine)}. END acquitté.</p>
    <div class="table-scroll"><table aria-label="Emplacements OEM en lecture seule"><thead><tr><th>Slot</th><th>Nom</th><th>RX · MHz</th><th>TX · MHz</th><th>Mode · bits OEM</th><th>Puissance · bits OEM</th></tr></thead><tbody>${snapshot.slots.map(slot => `<tr><td>${slot.slot}</td><td>${benchEscape(slot.name ?? 'Nom non interprétable')}</td><td class="freq">${slot.rxHz === null ? 'Inconnue' : formatMHz(slot.rxHz)}</td><td class="freq">${slot.txHz === null ? 'Inconnue' : formatMHz(slot.txHz)}</td><td>${benchEscape(slot.mode)}</td><td>${benchEscape(slot.power)}</td></tr>`).join('')}</tbody></table></div>
    <p class="help">32 emplacements bruts, pas une liste certifiée de canaux actifs. CTCSS, largeur, zones et interdiction TX ne sont pas décodés. Aucune donnée n’est injectée dans votre codeplug éditable.</p>`;
}
function benchControls(busy: boolean): void {
  benchDialog.querySelectorAll<HTMLButtonElement | HTMLSelectElement>('#bench-read, #bench-page, #bench-export').forEach(control => { control.disabled = busy || (control.id === 'bench-export' && !oemSnapshot); });
  benchDialog.querySelector<HTMLButtonElement>('#bench-cancel')!.disabled = !busy;
  benchDialog.querySelectorAll<HTMLButtonElement>('[data-bench-close]').forEach(button => { button.disabled = busy; });
}
async function readBenchPage(): Promise<void> {
  if (benchBusy) return;
  const page = Number(benchDialog.querySelector<HTMLSelectElement>('#bench-page')!.value);
  benchBusy = true; benchAbort = new AbortController(); benchControls(true);
  const progress = benchDialog.querySelector<HTMLProgressElement>('#bench-progress')!;
  progress.value = 0;
  benchMessage('Connexion à l’API du banc, identification et lecture…');
  try {
    const api = new BenchHttpApi({ signal: benchAbort.signal });
    await api.initialize();
    const client = new OemReadOnlyClient((path, data) => api.request(path, data), {
      signal: benchAbort.signal, spentEngine: spentEngine(),
      markEngine: engine => { oemSpentEngine = engine; try { sessionStorage.setItem(SPENT_ENGINE_KEY, engine); } catch { /* Keep the in-memory guard when storage is unavailable. */ } },
      progress: (done, total) => { progress.value = done / total; benchMessage(`D578UV identifié · lecture ${Math.round(100 * done / total)} %`); },
    });
    oemSnapshot = await client.readPage(page); renderOemSnapshot();
    benchMessage('Lecture terminée. Redémarrez le moteur du banc avant une nouvelle lecture. Votre codeplug éditable n’a pas été modifié.');
  } catch (error) {
    benchMessage(benchAbort.signal.aborted ? 'Lecture interrompue localement. Une commande déjà envoyée peut encore être traitée : redémarrez le moteur du banc avant de reprendre.' : `${(error as Error).message}\nAprès une session engagée, redémarrez le moteur du banc avant de reprendre. Aucun nouvel instantané n’est validé.`, true);
  } finally { benchBusy = false; benchAbort = null; benchControls(false); }
}
function exportOemSnapshot(): void {
  if (!oemSnapshot) return;
  const source = JSON.stringify({ format: 'opend578-oem-readonly-v1', ...oemSnapshot }, null, 2);
  const url = URL.createObjectURL(new Blob([source], { type: 'application/json' }));
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = `OpenD578-OEM-slots-${oemSnapshot.page * 32 + 1}-${oemSnapshot.page * 32 + 32}.json`;
  document.body.append(anchor); anchor.click(); anchor.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function openBenchPanel(): void {
  const sameOrigin = isBenchPage();
  benchDialog.innerHTML = `<div class="dialog-head"><h2 id="bench-title">Banc émulé · lecture OEM</h2><button data-bench-close aria-label="Fermer">×</button></div>
    <div class="dialog-body"><p class="help">Adaptateur de recherche D578UV, profil OEM V1.21. Le firmware RX FM alpha ne fournit pas encore les commandes CPS. Fermez le CPS intégré et tout pont externe : un seul client USB à la fois.</p>
    ${sameOrigin ? `<div class="toolbar"><label class="field">Groupe d’emplacements<select id="bench-page"><option value="0">1–32</option><option value="1">33–64</option><option value="2">65–96</option><option value="3">97–128</option></select></label><div class="actions"><button id="bench-read" class="primary">Identifier et lire</button><button id="bench-cancel" disabled>Interrompre</button><button id="bench-export" disabled>Exporter l’instantané</button></div></div><progress id="bench-progress" max="1" value="0" aria-label="Progression de lecture"></progress><div id="bench-status" class="notice" role="status">Démarrez le firmware OEM dans le banc avant de lire. Aucune commande d’écriture de codeplug n’est envoyée. PROGRAM et END ouvrent et ferment la session de programmation.</div><div id="bench-results"></div>` : `<p>Pour conserver la protection du banc, le CPS connecté doit être ouvert depuis sa propre adresse.</p><form id="bench-open-form"><label class="field">Adresse locale affichée par le banc Python<input id="bench-url" type="url" value="http://127.0.0.1:8765" required></label><p class="help">Le banc doit être mis à jour avec cette branche et le CPS compilé (npm run build). Le simulateur GitHub Pages n’expose pas cette API HTTP.</p><p class="help">Le nouvel onglet utilise une session de navigateur distincte de celle de ce fichier HTML. Exportez votre JSON si vous souhaitez le déplacer ; la lecture OEM reste une inspection séparée.</p><div id="bench-status" class="notice" role="status">Aucune connexion n’est faite depuis ce fichier.</div><button class="primary" type="submit">Ouvrir le CPS dans le banc</button></form>`}
    </div><div class="dialog-footer"><button data-bench-close>Fermer</button></div>`;
  benchDialog.querySelectorAll('[data-bench-close]').forEach(button => button.addEventListener('click', () => benchDialog.close()));
  if (sameOrigin) {
    benchDialog.querySelector('#bench-read')!.addEventListener('click', () => { void readBenchPage(); });
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
benchDialog.addEventListener('cancel', event => { if (benchBusy) { event.preventDefault(); benchAbort?.abort(new Error('Lecture annulée')); } });
window.addEventListener('beforeunload', event => { if (benchBusy) { event.preventDefault(); event.returnValue = ''; } });
