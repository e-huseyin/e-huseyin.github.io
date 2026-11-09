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
// A6 verticale (testi centrati) e A7 orizzontale (testi a sinistra, QR a destra). Modelli: tools/palette_build.py
const SIZES = {
  a6: {label: 'A6', x: '525', nameMax: 910, nameSizes: [70, 55, 43, 34, 28],
       wrap: 36, maxLines: 4, affMax: 900, affSize: [29, 29, 24, 21], affY: [1032, 1013, 996, 993]},
  a7: {label: 'A7', x: '56', nameMax: 760, nameSizes: [56, 46, 38, 30, 26],
       wrap: 50, maxLines: 2, affMax: 760, affSize: [26, 24], affY: [666, 660]},
};
let size = 'a6';
sizeButtons.forEach(b => b.addEventListener('click', () => {
  size = b.dataset.size;
  sizeButtons.forEach(x => x.setAttribute('aria-pressed', String(x === b)));
  updateBlank(); draw();
}));

// ---- Combinazioni di colore: cambiano pagina e file scaricabili (non il programma)
const PALETTES = window.AF26_PALETTES;
const select = document.getElementById('palette');
let palette = 'grafite-bordeaux';  // predefinita
try { const saved = localStorage.getItem('af26-palette'); if (PALETTES[saved]) palette = saved; } catch (e) {}
const paint = tpl => ['INK', 'ACC', 'NODE', 'ACC2'].reduce((s, k) => s.split('{{' + k + '}}').join(PALETTES[palette][k]), tpl);
function updateBlank(){
  blank.href = 'assets/palette/' + palette + '/badge-' + size + '.svg';
  blank.download = 'ArcheoFOSS2026-badge-vuoto-' + SIZES[size].label + '-' + palette + '.svg';
}
function applyPalette(){
  document.documentElement.dataset.palette = palette;
  select.value = palette;
  document.querySelectorAll('[data-asset]').forEach(n => {
    const file = 'assets/palette/' + palette + '/' + n.dataset.asset;
    if (n.tagName === 'IMG' || n.tagName === 'IFRAME') n.src = file;
    else {
      n.href = file;
      if (n.hasAttribute('download')) n.download = 'ArcheoFOSS2026-' + n.dataset.asset.replace(/\.(\w+)$/, '-' + palette + '.$1');
    }
  });
  updateBlank(); draw();
}
select.addEventListener('change', () => {
  palette = select.value;
  try { localStorage.setItem('af26-palette', palette); } catch (e) {}
  applyPalette();
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

  // Affiliazione: A6 fino a quattro righe, A7 fino a due
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
  const a = document.createElement('a'); a.href = url; a.download = 'ArcheoFOSS2026-badge-' + SIZES[size].label + '-' + safe + '-' + palette + '.svg';
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}
nameInput.addEventListener('input', draw);
affInput.addEventListener('input', draw);
roleInput.addEventListener('change', draw);
document.getElementById('badge-download').addEventListener('click', download);
applyPalette();
})();
