/* Animate sheets, traced area and its share on one shared timeline. */
window.RevealContactTracing = {
  id: 'rupe-contact-tracing',
  init(reveal) {
    const slide = document.querySelector('#contact-tracing');
    if (!slide) return;
    const data = slide.querySelector('.contact-data');
    const number = slide.querySelector('[data-contact-area-count]');
    const sheets = slide.querySelector('[data-contact-sheet-count]');
    const fill = slide.querySelector('.contact-area-fill');
    const percentage = slide.querySelector('.contact-secondary-percentage strong');
    if (!data || !number || !sheets || !fill || !percentage) return;
    const target = 342;
    const share = target / (84 * 35) * 100;
    const duration = 1500;
    let frame = null;
    let shown = false;
    const paint = progress => {
      sheets.textContent = String(Math.round(780 * progress));
      number.textContent = String(Math.round(target * progress));
      fill.style.width = `${share * progress}%`;
      percentage.textContent = `≈ ${(share * progress).toFixed(1)}%`;
    };
    const cancel = () => {
      if (frame !== null) cancelAnimationFrame(frame);
      frame = null;
    };
    const sync = () => {
      const visible = reveal.isPrintView?.() ||
        (reveal.getCurrentSlide() === slide && data.classList.contains('visible'));
      if (!visible) {
        cancel();
        shown = false;
        paint(0);
        return;
      }
      if (shown) return;
      shown = true;
      if (reveal.isPrintView?.() || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        paint(1);
        return;
      }
      paint(0);
      let start;
      const tick = now => {
        if (start === undefined) start = now;
        const progress = Math.min(1, (now - start) / duration);
        // A shared ease-in-out keeps the number and bar proportional.
        paint(progress * progress * (3 - 2 * progress));
        frame = progress < 1 ? requestAnimationFrame(tick) : null;
      };
      frame = requestAnimationFrame(tick);
    };
    ['ready', 'slidechanged', 'fragmentshown', 'fragmenthidden'].forEach(event => reveal.on(event, sync));
    paint(0);
    sync();
  }
};
