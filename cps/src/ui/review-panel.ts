import { reviewCodeplug } from '../core/channel-tools.ts';

export function openReviewPanel(value: unknown, proceed?: () => void): void {
  const panel = document.querySelector<HTMLDialogElement>('#review-dialog')!;
  const findings = reviewCodeplug(value), errors = findings.filter(item => item.severity === 'error').length;
  panel.innerHTML = '<div class="dialog-head"><h2 id="review-title">Bilan du codeplug</h2><button type="button" data-close aria-label="Fermer">×</button></div><div class="dialog-body"><p id="review-summary"></p><p class="help">Validation du fichier PC uniquement. Les bandes, capacités et puissances réelles ne sont pas connues tant que le contrat firmware n’est pas raccordé.</p><div id="review-findings"></div></div><div class="dialog-footer"><button type="button" data-close>Fermer</button></div>';
  panel.querySelector('#review-summary')!.textContent = `${errors} erreur(s) · ${findings.length - errors} avertissement(s). ${errors ? 'Export bloqué.' : 'Le document peut être exporté.'}`;
  for (const finding of findings) {
    const box = document.createElement('p'); box.className = `notice ${finding.severity === 'error' ? 'error' : ''}`;
    box.textContent = `${finding.severity === 'error' ? 'Erreur' : 'Avertissement'} · ${finding.path}\n${finding.message}`;
    panel.querySelector('#review-findings')!.append(box);
  }
  panel.querySelectorAll('[data-close]').forEach(button => button.addEventListener('click', () => panel.close()));
  if (proceed && !errors) {
    const button = document.createElement('button'); button.type = 'button'; button.className = 'primary'; button.textContent = 'Exporter malgré les avertissements';
    button.addEventListener('click', () => { panel.close(); proceed(); }); panel.querySelector('.dialog-footer')!.append(button);
  }
  panel.showModal();
}
