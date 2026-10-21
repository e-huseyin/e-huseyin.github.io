/* Local vector map: Reveal fragments drive a reversible geographic camera. */
window.RevealContextMap = (() => {
  const states = new WeakMap();
  const matrix = values => `matrix(${values.join(' ')})`;
  const ZOOM_MS = 1450, BOUNDARIES_MS = 450;
  const formatCount = new Intl.NumberFormat('en-GB');

  function drawInventory(state, values) {
    state.inventoryValues = values;
    state.count.textContent = formatCount.format(Math.round(values.count));
    state.ring.setAttribute('stroke-dashoffset', String(1 - values.sweep));
    state.ring.setAttribute('opacity', String(.7 * (1 - values.split)));
    state.segments.forEach(segment => {
      const length = Number(segment.dataset.inventoryShare) * values.split;
      segment.setAttribute('stroke-dasharray', `${length} 1`);
    });
  }

  function updateInventory(state, phase, immediate) {
    if (state.inventoryPhase === phase && !immediate) return;
    state.inventoryPhase = phase;
    cancelAnimationFrame(state.inventoryFrame);
    const total = Number(state.chart.dataset.recordedMarks);
    const significant = Number(state.chart.dataset.significantFigures);
    const target = {
      count: phase < 0 ? 0 : phase === 0 ? total : significant,
      sweep: phase < 0 ? 0 : phase === 1 ? significant / total : 1,
      split: phase === 2 ? 1 : 0
    };
    state.chart.setAttribute('aria-hidden', String(phase < 0));
    state.label.textContent = phase < 1 ? 'recorded marks' : 'significant figures';
    state.chart.setAttribute('aria-label', phase < 1
      ? `${formatCount.format(total)} recorded marks in the 1995 inventory`
      : `${formatCount.format(significant)} significant figures${phase === 2 ? '; published category percentages; 23 zoomorphs' : '; dot groups and scattered pecking excluded'}`);
    state.breakdown.forEach(node => node.setAttribute('aria-hidden', String(phase !== 2)));
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (immediate || reduced || phase < 0) {
      drawInventory(state, target);
      return;
    }
    const from = { ...state.inventoryValues };
    const duration = phase === 0 ? 1300 : phase === 1 ? 1100 : 1000;
    const start = performance.now();
    const tick = now => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      const current = {};
      Object.keys(target).forEach(key => current[key] = from[key] + (target[key] - from[key]) * eased);
      drawInventory(state, current);
      if (t < 1) state.inventoryFrame = requestAnimationFrame(tick);
    };
    state.inventoryFrame = requestAnimationFrame(tick);
  }

  function draw(state, values) {
    state.values = values;
    state.camera.setAttribute('transform', matrix(values));
    state.pins.forEach(pin => {
      const [x, y] = pin.dataset.point.split(' ').map(Number);
      pin.setAttribute('transform', `translate(${values[0] * x + values[4]} ${values[3] * y + values[5]})`);
    });
  }

  function update(slide, immediate = false) {
    const state = states.get(slide);
    if (!state) return;
    const visible = index => !!slide.querySelector(`[data-context-step="${index}"].visible`);
    const regional = visible(0), road = regional, counts = visible(1);
    const significant = counts && visible(2), breakdown = significant && visible(3);
    const animals = breakdown && visible(4);
    slide.classList.toggle('context-static', immediate);
    slide.classList.toggle('context-regional', regional);
    slide.classList.toggle('context-road', road);
    slide.classList.toggle('context-counts', counts);
    slide.classList.toggle('context-significant', significant);
    slide.classList.toggle('context-breakdown', breakdown);
    slide.classList.toggle('context-animals', animals);
    state.animals.setAttribute('aria-hidden', String(!animals));
    state.mapLayers.forEach(layer => layer.setAttribute('aria-hidden', String(animals)));
    updateInventory(state, !counts ? -1 : breakdown ? 2 : significant ? 1 : 0, immediate);
    const target = regional ? state.regional : state.overview;
    const key = regional ? 'regional' : 'overview';
    if (state.target === key && !immediate) return;
    state.target = key;
    cancelAnimationFrame(state.frame);
    const from = state.values.slice();
    const duration = immediate || matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : ZOOM_MS;
    const start = performance.now();
    const tick = now => {
      const t = duration ? Math.min(1, (now - start) / duration) : 1;
      const eased = 1 - Math.pow(1 - t, 3);
      draw(state, target.map((value, i) => from[i] + (value - from[i]) * eased));
      if (t < 1) state.frame = requestAnimationFrame(tick);
    };
    state.frame = requestAnimationFrame(tick);
  }

  return {
    id: 'context-map',
    init(reveal) {
      reveal.getSlides().filter(slide => slide.matches('.rupe-context')).forEach(slide => {
        slide.style.setProperty('--map-zoom-duration', `${ZOOM_MS}ms`);
        slide.style.setProperty('--map-boundary-duration', `${BOUNDARIES_MS}ms`);
        slide.style.setProperty('--map-road-delay', `${ZOOM_MS + BOUNDARIES_MS}ms`);
        const svg = slide.querySelector('.context-map');
        const overview = svg.dataset.overview.split(' ').map(Number);
        const regional = svg.dataset.regional.split(' ').map(Number);
        const chart = slide.querySelector('[data-inventory-chart]');
        const state = {
          camera: svg.querySelector('.map-camera'), pins: [...svg.querySelectorAll('.map-pin')],
          overview, regional, values: overview.slice(), frame: 0,
          chart, count: chart.querySelector('[data-inventory-count]'),
          label: chart.querySelector('[data-inventory-count-label]'),
          ring: chart.querySelector('[data-inventory-ring]'),
          segments: [...chart.querySelectorAll('[data-inventory-share]')],
          breakdown: [...chart.querySelectorAll('[data-inventory-breakdown]')],
          animals: slide.querySelector('[data-context-animals]'),
          mapLayers: [...slide.querySelectorAll('[data-context-map-layer]')],
          inventoryValues: { count: 0, sweep: 0, split: 0 }, inventoryFrame: 0
        };
        states.set(slide, state);
        draw(state, overview);
      });
      reveal.on('ready', event => update(event.currentSlide, true));
      reveal.on('slidechanged', event => update(event.currentSlide, true));
      reveal.on('fragmentshown', event => update(event.fragment.closest('section')));
      reveal.on('fragmenthidden', event => update(event.fragment.closest('section')));
    }
  };
})();
