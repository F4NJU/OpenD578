/* F1DMG: display historically linked image files beside their explanatory text. */
(() => {
  'use strict';
  document.querySelectorAll('.f1dmg-original a.f1dmg-image-link').forEach((link) => {
    // An <a href="picture.jpg"> with only text previously looked like an ordinary link.
    // Preserve the text and insert the original image at that exact position.
    if (link.querySelector('img')) return;
    const caption = link.textContent.trim();
    const photo = document.createElement('img');
    photo.src = link.href;
    photo.alt = caption || 'Photographie liée depuis la page F1DMG';
    photo.loading = 'lazy';
    photo.decoding = 'async';
    link.replaceChildren(photo);
    if (caption) {
      const label = document.createElement('span');
      label.className = 'f1dmg-link-caption';
      label.textContent = caption;
      link.append(label);
    }
    link.classList.add('f1dmg-linked-photo');
  });

  const search = document.getElementById('f1dmg-search');
  const category = document.getElementById('f1dmg-category');
  const cards = [...document.querySelectorAll('#f1dmg-grid .f1dmg-photo')];
  const count = document.getElementById('f1dmg-count');
  const update = () => {
    const term = (search?.value || '').trim().toLowerCase();
    const selected = category?.value || '';
    let visible = 0;
    for (const card of cards) {
      const show = (!term || (card.dataset.search || '').includes(term)) &&
                   (!selected || (card.dataset.category || '') === selected);
      card.hidden = !show;
      if (show) visible++;
    }
    if (count) count.textContent = `${visible} / ${cards.length} image(s)`;
  };
  search?.addEventListener('input', update);
  category?.addEventListener('change', update);
  update();

  // Images embedded directly in historical paragraphs are zoomable, without
  // any remote script, analytics, uploading or backend dependency.
  if (typeof HTMLDialogElement !== 'undefined') {
    const dialog = document.createElement('dialog');
    dialog.className = 'f1dmg-lightbox';
    const close = document.createElement('button');
    close.type = 'button';
    close.textContent = 'Fermer';
    const image = document.createElement('img');
    image.alt = '';
    dialog.append(close, image);
    document.body.append(dialog);
    close.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
    document.querySelectorAll('.f1dmg-original .f1dmg-embedded-photo img').forEach((img) => {
      img.tabIndex = 0;
      img.setAttribute('role', 'button');
      img.setAttribute('aria-label', `Agrandir : ${img.alt || 'photo'}`);
      const open = () => {
        image.src = img.src;
        image.alt = img.alt;
        dialog.showModal();
      };
      img.addEventListener('click', open);
      img.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(); }
      });
    });
  }
})();
