/* Measure the actual bibliography after fonts load, preserving the 34 px margin. */
window.RevealReferences = {
  id: 'rupe-references',
  init(reveal) {
    const footers = [...document.querySelectorAll('.slide-references')];
    const setHeight = (footer, height) => {
      if (height > 0) footer.closest('section').style.setProperty('--reference-band', `${Math.ceil(height)}px`);
    };
    const measure = () => {
      const scale = reveal.getScale() || 1;
      footers.forEach(footer => setHeight(footer, footer.getBoundingClientRect().height / scale));
    };
    const observer = new ResizeObserver(entries => entries.forEach(entry => setHeight(entry.target, entry.contentRect.height)));
    footers.forEach(footer => observer.observe(footer));
    reveal.on('ready', measure);
    reveal.on('slidechanged', measure);
    reveal.on('resize', measure);
    document.fonts.ready.then(measure);
  }
};
