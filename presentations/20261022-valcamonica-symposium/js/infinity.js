/* INFINITY reveal.js template: behaviour shared by every deck.
 *
 * Registered as a reveal.js plugin *after* RevealMarkdown, so it runs once the
 * Markdown has been turned into <section>s and before backgrounds are built:
 *   - numbers chapters and gives each slide its chapter accent (acc-1..3)
 *   - adds a discreet page number at the bottom right, except on the cover
 *   - paints dark / light backgrounds (add class="light" to a slide)
 *   - draws the starburst rays on slides with class "rays" / "rays-dashed"
 * and, while presenting:
 *   - counts up [data-count] numbers and types .typewriter text on arrival
 *   - "L" flips every slide between the dark and light variant
 */
window.RevealInfinity = (() => {
  const INK = '#282828', PAPER = '#ffffff';
  const still = () => matchMedia('(prefers-reduced-motion: reduce)').matches
    || document.documentElement.classList.contains('reveal-print');

  // Rays of the template's starburst, centred on (1010, 380) of the 1280×720 canvas
  const RAYS = [[1080,378,1430,367],[1010,380,1257,460],[1010,380,1232,515],[1060,429,1652,1010],
    [1044,441,1135,608],[1010,380,1272,1551],[1010,380,747,1551],[1010,380,625,1194],[1010,380,824,562],
    [1010,380,665,620],[1010,380,-145,704],[1010,380,-187,463],[1010,380,-149,68],[1010,380,8,-280],
    [964,327,224,-526],[984,315,676,-456],[1010,380,940,-34],[1010,380,1084,-33],[1040,317,1523,-705],
    [1031,359,1643,-260],[1010,380,1231,244],[1039,372,1413,263]];

  function raysSvg() {
    const paths = RAYS.map(([x1, y1, x2, y2], i) =>
      `<path pathLength="1" style="--i:${i}" d="M${x1} ${y1}L${x2} ${y2}"/>`).join('');
    return `<svg class="rays-svg" viewBox="0 0 1280 720" aria-hidden="true" data-id="rays"><g>${paths}</g></svg>`;
  }

  function paint(slide) {
    slide.setAttribute('data-background-color', slide.classList.contains('light') ? PAPER : INK);
  }

  function decorate(reveal) {
    // stack parents are not tagged .stack yet at plugin time, so drop them by hand
    const slides = reveal.getSlides().filter(s => !s.querySelector('section'));
    const deckTitle = document.querySelector('.l-cover h1')?.textContent.trim() || document.title;
    let chapter = 0, chapterTitle = deckTitle;

    slides.forEach((slide, i) => {
      if (slide.classList.contains('l-chapter')) {
        chapter = +(slide.dataset.chapter || chapter + 1);
        chapterTitle = slide.querySelector('h1')?.textContent.trim() || chapterTitle;
      }
      // agenda recaps belong to the chapter they introduce
      const own = slide.classList.contains('l-agenda') ? 0 : chapter;
      if (own && ![...slide.classList].some(c => c.startsWith('acc-'))) slide.classList.add('acc-' + own);

      if (slide.matches('.rays, .rays-dashed')) slide.insertAdjacentHTML('afterbegin', raysSvg());

      if (!slide.matches('.l-cover')) {
        slide.insertAdjacentHTML('beforeend',
          `<footer class="page-number" aria-label="Slide ${i + 1}">${i + 1}</footer>`);
      }
      paint(slide);
    });
  }

  // ── on-arrival effects ──
  const timers = new Set();
  const later = (fn, ms) => { const t = setTimeout(() => { timers.delete(t); fn(); }, ms); timers.add(t); };

  function countUp(el) {
    const to = +el.dataset.count, suffix = el.dataset.suffix || '';
    if (still()) { el.textContent = to + suffix; return; }
    const t0 = performance.now(), dur = +(el.dataset.duration || 1400);
    const tick = now => {
      const k = Math.min(1, (now - t0) / dur), eased = 1 - Math.pow(1 - k, 3);
      el.textContent = Math.round(to * eased) + suffix;
      if (k < 1 && el.closest('.present')) requestAnimationFrame(tick);
      else el.textContent = to + suffix;
    };
    requestAnimationFrame(tick);
  }

  function typeOut(el) {
    const text = el.dataset.text ??= el.textContent.trim();
    el.setAttribute('aria-label', text);
    if (still()) { el.textContent = text; return; }
    el.textContent = '';
    el.classList.add('typing');
    let n = 0;
    const step = () => {
      if (!el.closest('.present')) { el.textContent = text; el.classList.remove('typing'); return; }
      el.textContent = text.slice(0, ++n);
      if (n < text.length) later(step, text[n - 1] === ',' ? 260 : 42);
      else later(() => el.classList.remove('typing'), 1600);
    };
    later(step, +(el.dataset.delay || 500));
  }

  function arrive(slide) {
    timers.forEach(clearTimeout); timers.clear();
    slide.querySelectorAll('[data-count]').forEach(countUp);
    slide.querySelectorAll('.typewriter').forEach(typeOut);
  }

  function toggleVariant(reveal) {
    reveal.getSlides().filter(s => !s.querySelector('section'))
      .forEach(s => { s.classList.toggle('light'); paint(s); });
    reveal.sync();
  }

  return {
    id: 'infinity',
    init(reveal) {
      decorate(reveal);
      reveal.addKeyBinding({ keyCode: 76, key: 'L', description: 'Toggle light / dark variant' },
        () => toggleVariant(reveal));
      reveal.on('ready', e => arrive(e.currentSlide));
      reveal.on('slidechanged', e => arrive(e.currentSlide));
      // icons are keyboard-reachable so their micro-animations are too
      document.querySelectorAll('.icons .material-symbols-sharp').forEach(icon => {
        icon.tabIndex = 0;
        icon.setAttribute('role', 'img');
        icon.setAttribute('aria-label', icon.dataset.name || icon.textContent.trim().replace(/_/g, ' '));
      });
    }
  };
})();
