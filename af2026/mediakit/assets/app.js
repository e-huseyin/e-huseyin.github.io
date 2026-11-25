/* Media kit a pagina singola: pulsanti in alto e badge personalizzabile. Nessuna dipendenza. */
(function(){
'use strict';

// ---- Pulsanti in alto: mostrano una sezione alla volta nella stessa pagina
const views = [...document.querySelectorAll('.view')];
const tabs = [...document.querySelectorAll('.tabs a')];
function show(){
  const id = location.hash.slice(1);
  const current = views.find(v => v.id === id) ? id : views[0].id;
  views.forEach(v => { v.hidden = v.id !== current; });
  tabs.forEach(t => t.setAttribute('aria-current', t.dataset.view === current ? 'page' : 'false'));
  window.scrollTo(0, 0);
}
window.addEventListener('hashchange', show);
show();

// ---- Badge: lo stesso SVG serve per anteprima e download
const preview = document.getElementById('badge-preview');
const nameInput = document.getElementById('badge-name-input');
const affInput = document.getElementById('badge-affiliation-input');
const blank = document.getElementById('badge-blank');
// Un solo badge A7 orizzontale, definitivo (modello: tools/palette_build.py): nome centrato; affiliazione in maiuscolo
// su una riga vicino alla fascia rosso mattone. Nessuna tipologia.
const S = {nameMax: 920, nameSizes: [72, 58, 46, 36, 30], affMax: 920};

// ---- Una sola combinazione di colore: Nero · Rosso mattone · Blu. I file scaricati hanno il loro nome esatto.
const PALETTES = window.AF26_PALETTES;
const palette = 'nero-mattone';
const paint = tpl => ['INK', 'ACC', 'NODE', 'ACC2'].reduce((s, k) => s.split('{{' + k + '}}').join(PALETTES[palette][k]), tpl);
function updateBlank(){
  blank.href = 'assets/palette/' + palette + '/badge.svg';
  blank.download = 'badge.svg';
}
function applyPalette(){
  document.documentElement.dataset.palette = palette;
  document.querySelectorAll('[data-asset]').forEach(n => {
    const file = 'assets/palette/' + palette + '/' + n.dataset.asset;
    if (n.tagName === 'IMG' || n.tagName === 'IFRAME') n.src = file;
    else {
      n.href = file;
      if (n.hasAttribute('download')) n.download = n.dataset.asset;
    }
  });
  updateBlank(); draw();
}

// ---- Download: i pulsanti scaricano il file invece di aprirlo (anche SVG, PDF, HTML)
// Il file viene letto e salvato con il suo nome esatto. Se il browser non lo permette
// (pagina aperta con doppio clic da file://), resta il comportamento normale del link.
document.addEventListener('click', e => {
  const a = e.target.closest('a[download]');
  if (!a || !a.href || a.href.startsWith('blob:') || a.target === '_blank' || location.protocol === 'file:') return;
  e.preventDefault();
  const name = a.getAttribute('download') || decodeURIComponent(a.href.split('/').pop().split('?')[0]);
  fetch(a.href).then(r => { if (!r.ok) throw new Error(r.status); return r.blob(); }).then(blob => {
    const url = URL.createObjectURL(new Blob([blob], {type: 'application/octet-stream'}));
    const t = document.createElement('a');
    t.href = url; t.download = name; t.style.display = 'none';
    document.body.appendChild(t); t.click(); t.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  }).catch(() => { window.location.href = a.href; });
});

function buildBadge(){
  const doc = new DOMParser().parseFromString(paint(window.AF26_BADGE.badge), 'image/svg+xml');
  const nm = doc.getElementById('badge-name');
  const aff = doc.getElementById('badge-affiliation');
  const name = nameInput.value.trim() || 'YOUR NAME';
  const affiliation = affInput.value.trim() || 'YOUR AFFILIATION';

  // Nome centrato: si rimpicciolisce se è lungo
  nm.textContent = name;
  const length = [...name].length;
  const step = length > 48 ? 4 : length > 36 ? 3 : length > 27 ? 2 : length > 19 ? 1 : 0;
  const nameSize = S.nameSizes[step];
  nm.setAttribute('font-size', String(nameSize));
  nm.removeAttribute('textLength'); nm.removeAttribute('lengthAdjust');
  if (length * nameSize * .57 > S.nameMax){ nm.setAttribute('textLength', String(S.nameMax)); nm.setAttribute('lengthAdjust', 'spacingAndGlyphs'); }

  // Affiliazione in maiuscolo, una riga; se è lunga si rimpicciolisce e poi si stringe
  const up = affiliation.toUpperCase(), len = [...up].length;
  const fs = Math.max(18, Math.min(28, Math.floor(S.affMax / (len * .72))));
  aff.textContent = up; aff.setAttribute('font-size', String(fs));
  aff.removeAttribute('textLength'); aff.removeAttribute('lengthAdjust');
  if (len * fs * .72 > S.affMax){ aff.setAttribute('textLength', String(S.affMax)); aff.setAttribute('lengthAdjust', 'spacingAndGlyphs'); }
  return doc.documentElement;
}
function draw(){ preview.replaceChildren(document.importNode(buildBadge(), true)); }
function download(){
  const src = new XMLSerializer().serializeToString(buildBadge());
  const url = URL.createObjectURL(new Blob([src], {type: 'image/svg+xml;charset=utf-8'}));
  const safe = (nameInput.value.trim() || 'badge').normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-zA-Z0-9 -]/g, '').replace(/\s+/g, '-').slice(0, 60) || 'badge';
  const a = document.createElement('a'); a.href = url; a.download = 'badge-' + safe + '.svg';
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}
nameInput.addEventListener('input', draw);
affInput.addEventListener('input', draw);
document.getElementById('badge-download').addEventListener('click', download);
applyPalette();
})();
