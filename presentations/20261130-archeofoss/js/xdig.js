/* X-DigCheck deck widgets, registered as a reveal.js plugin (after RevealInfinity).
 * Everything is built in init(), before reveal.js reads the fragments, so fragments
 * created here (chart annotations) are picked up like the ones written in index.html.
 * Data: window.XDIG_DATA (js/xdig-data.js), exported from the RupeMagnaOnto dashboard. */
window.RevealXDig = (() => {
  const NS = 'http://www.w3.org/2000/svg';
  const D = window.XDIG_DATA;
  const still = () => matchMedia('(prefers-reduced-motion: reduce)').matches
    || document.documentElement.classList.contains('reveal-print');
  const el = (tag, attrs = {}, parent) => {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    if (parent) parent.append(n);
    return n;
  };
  const txt = (parent, x, y, s, cls = '', extra = {}) => { const t = el('text', { x, y, class: cls, ...extra }, parent); t.textContent = s; return t; };
  const fmt = (v, dec = 0) => v.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec });
  const svgRoot = (host, vb, cls, label) => el('svg', { viewBox: vb, class: cls, role: 'img', 'aria-label': label, preserveAspectRatio: 'xMidYMid meet' }, host);

  // ───────── count-up numbers: [data-num] (+ data-dec, data-pre, data-suf) ─────────
  function countUp(scope) {
    scope.querySelectorAll('[data-num]').forEach(b => {
      const frag = b.closest('.fragment');
      if (frag && !frag.classList.contains('visible')) return;
      const end = +b.dataset.num, dec = +(b.dataset.dec || 0), pre = b.dataset.pre || '', suf = b.dataset.suf || '';
      const show = v => { b.textContent = pre + fmt(v, dec) + suf; };
      if (still()) { show(end); return; }
      const t0 = performance.now(), dur = +(b.dataset.dur || 1500);
      const tick = now => {
        const k = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - k, 3);
        show(dec ? end * e : Math.round(end * e));
        if (k < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }

  // ───────── lightbox for img.zoom ─────────
  function lightbox(reveal) {
    const box = document.querySelector('.lightbox'); if (!box) return;
    const img = box.querySelector('img'), cap = box.querySelector('p');
    const close = () => box.classList.remove('open');
    document.querySelector('.reveal').addEventListener('click', e => {
      const t = e.target.closest('img.zoom'); if (!t) return;
      img.src = t.currentSrc || t.src; img.alt = t.alt; cap.textContent = t.alt;
      box.classList.add('open');
    }, true);
    box.addEventListener('click', close);
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && box.classList.contains('open')) { e.stopPropagation(); close(); } }, true);
    reveal.on('slidechanged', close);
  }

  // ───────── 8 · workflow (Figure 1 redrawn) ─────────
  function flow(host) {
    const svg = svgRoot(host, '0 0 640 530', 'fl', 'Co-evolution workflow: the data pipeline feeds semRTI, X-DigCheck checks coverage, shapes and CQs, then either a revision loops back or the KG and profile are stable');
    const defs = el('defs', {}, svg);
    [['fl-arr', ''], ['fl-arr-y', '']].forEach(([id]) => {
      const m = el('marker', { id, viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: 'auto-start-reverse' }, defs);
      el('path', { d: 'M0 0 L10 5 L0 10 z' }, m);
    });
    let n = 0;
    const box = (x, y, w, h, t, s, cls = '') => {
      const g = el('g', { class: `bx pop ${cls}`, style: `--i:${n++}; --d:150ms` }, svg);
      el('rect', { x, y, width: w, height: h, rx: 9 }, g);
      if (s) { txt(g, x + 14, y + h / 2 - 3, t, 't'); txt(g, x + 14, y + h / 2 + 13, s, 's'); } else txt(g, x + 14, y + h / 2 + 5, t, 't');
    };
    const ar = (d, cls = '', delay) => el('path', { d, class: `ar ${cls}`, style: delay ? `--d:${delay}` : '' }, svg);
    txt(svg, 10, 14, 'DATA', 'lane'); txt(svg, 270, 14, 'KNOWLEDGE', 'lane');
    const L = [['RTI capture', '48-light dome, RAW'], ['Darktable', 'RAW to JPEG'], ['Dataset', 'RAW, JPEG, exports'], ['RelightLab', 'PTM / HSH outputs'], ['Visualisation', 'RTIViewer, OpenLIME'], ['Human annotation', 'context, metadata description']];
    L.forEach(([t, s], i) => { const y = 26 + i * 70; box(10, y, 200, 50, t, s); if (i) ar(`M110 ${y - 19} V${y - 2}`); });
    const K = [['Ontology initiation', 'CHS-ODP / ArCo, CHAD-KG, CIDOC CRM', 'k'], ['semRTI: lifting + KG construction', 'SPARQL Anything, RelightLab plugin', 'k'], ['X-DigCheck', 'mutual ontology–data coverage', 'chk'], ['X-DigCheck + OWL2SHACL', 'shapes from restrictions and CQs', 'chk'], ['Validation', 'SHACL and SPARQL CQ tests', 'chk'], ['New iteration needed?', 'coverage, violations, CQ results', 'q']];
    K.forEach(([t, s, c], i) => { const y = 26 + i * 64; box(270, y, 280, 48, t, s, c); if (i) ar(`M410 ${y - 15} V${y - 2}`); });
    el('rect', { x: 262, y: 148, width: 296, height: 196, rx: 12, class: 'grp' }, svg);
    txt(svg, 566, 160, 'X-DIGCHECK', 'grpl', { transform: 'rotate(90 566 160)' });
    // Darktable, RelightLab and the human annotation feed semRTI (as in Fig. 1)
    [1, 3, 5].forEach(i => { const y = 51 + i * 70; ar(`M210 ${y} H238`, 'feed'); });
    ar('M238 401 V115 H268');
    box(270, 452, 280, 48, 'Revision', 'ontology, data, or mappings', 'k');
    box(10, 452, 200, 48, 'Stable KG + profile', '', 'ok');
    ar('M410 394 V450', '', '1.8s'); txt(svg, 418, 428, 'yes', 'lbl', { style: '--d:1.8s' });
    ar('M270 370 H252 V476 H212', '', '1.8s'); txt(svg, 230, 444, 'no', 'lbl', { style: '--d:1.8s' });
    ar('M550 476 H600 V114 H552', 'loop'); txt(svg, 612, 300, 'iterate', 'lbl', { transform: 'rotate(90 612 300)', style: '--d:2.6s' });
    svg.querySelectorAll('.feed').forEach(p => p.style.markerEnd = 'none');
  }

  // ───────── 10 · competency questions answered / asked, per run ─────────
  function cqbars(host) {
    const S = D.series, L = D.labels, N = L.length, W = 760, H = 116, top = 22, base = 92, max = 29;
    const svg = svgRoot(host, `0 0 ${W} ${H}`, 'cqb', 'Competency questions answered out of asked, per run: from 0 of 8 at iteration 0 to 26 of 28 at iteration 10');
    const step = W / N, bw = step * .56;
    L.forEach((l, i) => {
      const x = i * step + (step - bw) / 2, hA = S.nb_cq[i] / max * (base - top), hO = S.nb_valid_cq[i] / max * (base - top);
      el('rect', { x, y: base - hA, width: bw, height: hA, rx: 3, class: 'ask' }, svg);
      const r = el('rect', { x, y: base - hO, width: bw, height: Math.max(hO, .01), rx: 3, class: 'ok', style: `--i:${i}` }, svg);
      el('title', {}, r).textContent = `iteration ${l} · ${S.nb_valid_cq[i]} of ${S.nb_cq[i]} competency questions answered`;
      txt(svg, x + bw / 2, base - hA - 5, `${S.nb_valid_cq[i]}/${S.nb_cq[i]}`, 'v', { style: `--i:${i}` });
      txt(svg, x + bw / 2, base + 16, l, 'ax');
    });
    txt(svg, -8, base + 16, 'iter.', 'ax', { 'text-anchor': 'end' });
  }

  // ───────── 11 · validation health chart (Figure 2, exact values) ─────────
  function health(host) {
    const S = D.series, L = D.labels, N = L.length;
    const W = 1180, x0 = 74, x1 = 1060, yT = 46, yB = 352;
    const X = i => x0 + i * (x1 - x0) / (N - 1), Y = v => yB - v / 100 * (yB - yT);
    const svg = svgRoot(host, `0 0 ${W} 540`, 'hc draw', 'Line chart: competency questions answered and SHACL shapes conforming across 15 runs, from 0% and 43% at iteration 0 to 93% and 76% at iteration 10');
    // 3.x series shading
    const half = (x1 - x0) / (N - 1) / 2;
    el('rect', { x: X(3) - half, y: yT - 8, width: X(7) - X(3) + 2 * half, height: yB - yT + 8, class: 'shade' }, svg);
    txt(svg, (X(3) + X(7)) / 2, yT + 8, 'iteration 3 series', 'shade-l');
    const grid = el('g', { class: 'grid' }, svg);
    for (let v = 0; v <= 100; v += 20) { el('line', { x1: x0 - 10, x2: x1 + 10, y1: Y(v), y2: Y(v) }, grid); txt(svg, x0 - 18, Y(v) + 4, v + '%', 'ax y'); }
    L.forEach((l, i) => txt(svg, X(i), yB + 24, l, 'ax x'));
    txt(svg, x0 - 18, yB + 24, 'iter.', 'ax y');
    // KG size strip
    const sT = 420, sB = 500, maxT = 150000;
    txt(svg, x1 + 26, sB - 4, 'KG TRIPLES', 'strip-l');
    S.kg_triples.forEach((t, i) => {
      const h = Math.max(2, t / maxT * (sB - sT));
      const r = el('rect', { x: X(i) - 16, y: sB - h, width: 32, height: h, rx: 3, class: 'bar' + (t > 100000 ? ' big' : '') }, svg);
      el('title', {}, r).textContent = `iteration ${l(i)} · ${fmt(t)} triples`;
      const prev = S.kg_triples[i - 1];
      if (i === 0 || Math.abs(t - prev) / prev > .05) txt(svg, X(i), sB - h - 6, fmt(t), 'barv');
    });
    function l(i) { return L[i]; }
    // lines + points
    const series = [['cq', S.cq_pass_rate_pct, '300ms', '2.2s'], ['sh', S.shape_pass_rate_pct, '700ms', '2.2s']];
    series.forEach(([c, vals, d, dur]) => {
      el('path', { d: 'M' + vals.map((v, i) => `${X(i)} ${Y(v)}`).join(' L'), class: `ln ${c} d`, pathLength: 1, style: `--d:${d}; animation-duration:${dur}` }, svg);
    });
    series.forEach(([c, vals]) => vals.forEach((v, i) => el('circle', { cx: X(i), cy: Y(v), r: 6, class: `pt ${c}`, style: `--i:${i}; --d:${c === 'cq' ? 900 : 1100}ms` }, svg)));
    // end values
    txt(svg, X(N - 1) + 16, Y(S.cq_pass_rate_pct[N - 1]) + 4, S.cq_pass_rate_pct[N - 1] + '%', 'endv cq');
    txt(svg, X(N - 1) + 16, Y(S.shape_pass_rate_pct[N - 1]) + 8, S.shape_pass_rate_pct[N - 1] + '%', 'endv sh');
    // legend
    const lg = el('g', { class: 'lg' }, svg);
    el('rect', { x: x0, y: 6, width: 22, height: 6, rx: 3, class: 'cq' }, lg); txt(lg, x0 + 30, 14, 'competency questions answered');
    el('rect', { x: x0 + 270, y: 6, width: 22, height: 6, rx: 3, class: 'sh' }, lg); txt(lg, x0 + 300, 14, 'SHACL shapes conforming');
    // hover readout
    const rd = txt(svg, x0, 534, 'hover a run', 'rd');
    const guide = el('line', { x1: 0, x2: 0, y1: yT - 8, y2: sB, class: 'guide' }, svg);
    L.forEach((lab, i) => {
      const hit = el('rect', { x: X(i) - half, y: yT - 8, width: 2 * half, height: sB - yT + 8, class: 'hit' }, svg);
      hit.addEventListener('mouseenter', () => {
        guide.setAttribute('x1', X(i)); guide.setAttribute('x2', X(i)); guide.classList.add('on');
        rd.innerHTML = '';
        const parts = [['k', `iter ${lab}`], ['', `  ·  CQs ${S.nb_valid_cq[i]}/${S.nb_cq[i]} (${S.cq_pass_rate_pct[i]}%)  ·  shapes ${S.nb_validated_shapes[i]}/${S.nb_shapes[i]} (${S.shape_pass_rate_pct[i]}%)  ·  ${fmt(S.kg_triples[i])} triples`]];
        parts.forEach(([c, s]) => { const t = el('tspan', c ? { class: c } : {}, rd); t.textContent = s; });
      });
      hit.addEventListener('mouseleave', () => { guide.classList.remove('on'); rd.textContent = 'hover a run'; });
    });
    // annotations, revealed as fragments; boxes sit in areas the two lines never cross
    // ann([point x, y], [leader end x, y], box x, box y, box width, lines, fragment index)
    const ann = ([px, py], [ex, ey], lx, ly, w, lines, idx) => {
      const g = el('g', { class: 'ann fragment', 'data-fragment-index': idx }, svg);
      el('line', { x1: px, y1: py, x2: ex, y2: ey }, g);
      el('rect', { x: lx, y: ly, width: w, height: lines.length * 18 + 14 }, g);
      const t = txt(g, lx + 12, ly + 21, '');
      lines.forEach((s, k) => { const sp = el('tspan', { x: lx + 12, dy: k ? 18 : 0, class: k ? '' : 'h' }, t); sp.textContent = s; });
    };
    ann([X(1), Y(0)], [200, 317], 200, 292, 270,['0 / 8 CQs answered at iter 0–1', 'the 8 questions inherited from CHS-ODP'], 0);
    ann([X(5), Y(40)], [X(5), 186], 295, 118, 262, ['3.0–3.4: five revisions, one graph', 'ontology revised on an unchanged', 'KG of 78,773 triples'], 1);
    ann([X(11), Y(S.cq_pass_rate_pct[11])], [X(11), 250], 709, 250, 280, ['iter 7: CQs drop to 51.7% on a', 'smaller graph (4,457 triples); back up', 'once regenerated (iter 8 · 147,715)'], 2);
    ann([X(14), Y(92.9)], [990, 43], 758, 18, 232,['stable iteration 10', '26 / 28 CQs · 32 / 42 shapes'], 3);
  }

  // ───────── 14 · TBox vs ABox sparkline ─────────
  function lag(host) {
    const S = D.series, N = D.labels.length, W = 640, H = 130, p = 14;
    const X = i => p + i * (W - 2 * p) / (N - 1), Y = v => H - 18 - v / 85 * (H - 30);
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, class: 'lgs draw', role: 'img', 'aria-label': 'Classes declared in the profile versus classes used in the KG, per run', preserveAspectRatio: 'xMidYMid meet' });
    host.prepend(svg);
    // shaded gap where the TBox runs ahead of the ABox
    const top = S.onto_classes.map((v, i) => `${X(i)} ${Y(v)}`), bot = S.kg_classes.map((v, i) => `${X(i)} ${Y(v)}`).reverse();
    el('path', { d: 'M' + top.join(' L') + ' L' + bot.join(' L') + ' Z', class: 'gap' }, svg);
    el('line', { x1: p, x2: W - p, y1: H - 18, y2: H - 18, class: 'gl' }, svg);
    el('path', { d: 'M' + top.join(' L'), class: 't d', pathLength: 1, style: '--d:600ms; animation-duration:1.8s' }, svg);
    el('path', { d: 'M' + S.kg_classes.map((v, i) => `${X(i)} ${Y(v)}`).join(' L'), class: 'a d', pathLength: 1, style: '--d:900ms; animation-duration:1.8s' }, svg);
    D.labels.forEach((l, i) => { if (!l.includes('.') || l === '3.0') txt(svg, X(i), H - 3, l === '3.0' ? '3.x' : l, 'ax'); });
  }

  // ───────── 13 · demo stepper + typed terminals ─────────
  function demo(sec, reveal) {
    const rail = sec.querySelector('.rail'), lis = [...rail.querySelectorAll('li')], panes = [...sec.querySelectorAll('.pane')];
    const typers = new Map();
    panes.forEach(p => { const t = p.querySelector('[data-term]'); if (t) typers.set(p, t); });
    let timers = [];
    const type = term => {
      timers.forEach(clearTimeout); timers = [];
      const lines = term.dataset.term.split('|');
      term.innerHTML = '';
      const later = (fn, ms) => timers.push(setTimeout(fn, ms));
      let t = 250;
      lines.forEach(line => {
        const row = document.createElement('div');
        if (line.startsWith('#')) { row.innerHTML = `<span class="c"></span>`; } else { row.innerHTML = `<span class="p">$ </span><span class="cmd">python xdigcheck_cli.py </span><span class="arg"></span>`; }
        const target = row.querySelector(line.startsWith('#') ? '.c' : '.arg');
        later(() => term.append(row), t);
        if (still()) { target.textContent = line; return; }
        [...line].forEach((ch, k) => later(() => { target.textContent += ch; }, t + 300 + k * 38));
        t += 300 + line.length * 38 + 450;
      });
      later(() => { const c = document.createElement('span'); c.className = 'cur'; term.append(c); }, t);
    };
    const set = step => {
      sec.dataset.step = step;
      rail.style.setProperty('--p', step / 3);
      lis.forEach((li, i) => { li.classList.toggle('on', i === step); li.classList.toggle('done', i < step); });
      panes.forEach((p, i) => p.classList.toggle('on', i === step));
      const term = typers.get(panes[step]); if (term && sec.classList.contains('present')) type(term);
    };
    const sync = () => set(sec.querySelectorAll('.step-f.visible').length);
    reveal.on('fragmentshown', e => { if (sec.contains(e.fragment)) sync(); });
    reveal.on('fragmenthidden', e => { if (sec.contains(e.fragment)) sync(); });
    lis.forEach((li, i) => li.querySelector('button').addEventListener('click', e => {
      e.stopPropagation();
      const { h } = reveal.getIndices(sec); reveal.slide(h, 0, i - 1);
    }));
    set(0);
    return { arrive: sync, leave: () => { timers.forEach(clearTimeout); timers = []; } };
  }

  function qrs() {
    if (!window.QRCode) return;
    document.querySelectorAll('[data-qr]').forEach(n => {
      new QRCode(n, { text: n.dataset.qr, width: 256, height: 256, colorDark: '#1f2022', colorLight: '#ffffff', correctLevel: QRCode.CorrectLevel.M });
      n.title = n.dataset.qr;
    });
  }

  return {
    id: 'xdig',
    init(reveal) {
      const live = new Map(); // section → { arrive, leave }
      const own = (node, api) => { const s = node.closest('section'); if (s && api) live.set(s, api); };
      document.querySelectorAll('[data-flow]').forEach(flow);
      document.querySelectorAll('[data-health]').forEach(health);
      document.querySelectorAll('[data-lag]').forEach(lag);
      document.querySelectorAll('[data-cqbars]').forEach(cqbars);
      document.querySelectorAll('.x-demo').forEach(s => own(s, demo(s, reveal)));
      lightbox(reveal);
      qrs();
      let prev = null;
      const arrive = slide => {
        if (prev && prev !== slide) live.get(prev)?.leave?.();
        prev = slide;
        live.get(slide)?.arrive?.();
        countUp(slide);
      };
      reveal.on('ready', e => arrive(e.currentSlide));
      reveal.on('slidechanged', e => arrive(e.currentSlide));
      reveal.on('fragmentshown', e => { if (e.fragment.querySelector('[data-num]')) countUp(e.fragment); });
    }
  };
})();
