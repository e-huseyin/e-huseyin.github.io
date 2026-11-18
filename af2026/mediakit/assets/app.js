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
const roleInput = document.getElementById('badge-role-input');
const affInput = document.getElementById('badge-affiliation-input');
const blank = document.getElementById('badge-blank');
const sizeButtons = [...document.querySelectorAll('.size-switch button')];
// Badge A7 orizzontale: A7-01..03 con la fascia in basso, A7-04 con il QR. Modelli: tools/palette_build.py
const A7 = {x: '56', nameMax: 760, nameSizes: [56, 46, 38, 30, 26],
       wrap: 50, maxLines: 2, affMax: 760, affSize: [26, 24], affY: [666, 660]};
// A7-01..03: nome, affiliazione e tipologia centrati (modelli con la fascia rosso mattone in basso)
const MODEL = {x: '525', nameMax: 920, nameSizes: [72, 58, 46, 36, 30],
       wrap: 52, maxLines: 2, affMax: 920, affSize: [30, 26], affY: [452, 445]};
const SIZES = {'A7-01': {label: 'A7-01', ...MODEL},
               'A7-02': {label: 'A7-02', ...MODEL}, 'A7-03': {label: 'A7-03', ...MODEL}, 'A7-04': {label: 'A7-04', ...A7}};
let size = 'A7-01';
sizeButtons.forEach(b => b.addEventListener('click', () => {
  size = b.dataset.size;
  sizeButtons.forEach(x => x.setAttribute('aria-pressed', String(x === b)));
  updateBlank(); draw();
}));

// ---- Una sola combinazione di colore: Nero · Rosso mattone · Blu. I file scaricati hanno il loro nome esatto.
const PALETTES = window.AF26_PALETTES;
const palette = 'nero-mattone';
const paint = tpl => ['INK', 'ACC', 'NODE', 'ACC2'].reduce((s, k) => s.split('{{' + k + '}}').join(PALETTES[palette][k]), tpl);
function updateBlank(){
  blank.href = 'assets/palette/' + palette + '/badge-' + size + '.svg';
  blank.download = 'badge-' + size + '.svg';
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
  const S = SIZES[size];
  const doc = new DOMParser().parseFromString(paint(window.AF26_BADGE[size]), 'image/svg+xml');
  const nm = doc.getElementById('badge-name');
  const aff = doc.getElementById('badge-affiliation');
  const role = doc.getElementById('badge-role');
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

  if (!aff || !role) return doc.documentElement;
  // Affiliazione: fino a due righe
  const lines = []; let cur = '';
  for (const word of affiliation.split(/\s+/).filter(Boolean)){
    const next = cur ? cur + ' ' + word : word;
    if (cur && next.length > S.wrap){ lines.push(cur); cur = word; } else cur = next;
  }
  if (cur) lines.push(cur);
  const n = S.maxLines;
  const fin = lines.length > n ? [...lines.slice(0, n - 1), lines.slice(n - 1).join(' ')] : lines;
  aff.textContent = '';
  const k = Math.max(fin.length, 1) - 1;
  const affSize = S.affSize[k];
  aff.setAttribute('font-size', String(affSize));
  aff.setAttribute('y', String(S.affY[k]));
  fin.forEach((line, i) => {
    const t = doc.createElementNS('http://www.w3.org/2000/svg', 'tspan');
    t.setAttribute('x', S.x); if (i) t.setAttribute('dy', String(affSize + 5));
    if ([...line].length * affSize * .57 > S.affMax){ t.setAttribute('textLength', String(S.affMax)); t.setAttribute('lengthAdjust', 'spacingAndGlyphs'); }
    t.textContent = line; aff.appendChild(t);
  });
  role.textContent = roleInput.value.toUpperCase();
  return doc.documentElement;
}
function draw(){ preview.replaceChildren(document.importNode(buildBadge(), true)); }
function download(){
  const src = new XMLSerializer().serializeToString(buildBadge());
  const url = URL.createObjectURL(new Blob([src], {type: 'image/svg+xml;charset=utf-8'}));
  const safe = (nameInput.value.trim() || 'badge').normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-zA-Z0-9 -]/g, '').replace(/\s+/g, '-').slice(0, 60) || 'badge';
  const a = document.createElement('a'); a.href = url; a.download = 'badge-' + size + '-' + safe + '.svg';
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}
nameInput.addEventListener('input', draw);
affInput.addEventListener('input', draw);
roleInput.addEventListener('change', draw);
document.getElementById('badge-download').addEventListener('click', download);
applyPalette();
})();
