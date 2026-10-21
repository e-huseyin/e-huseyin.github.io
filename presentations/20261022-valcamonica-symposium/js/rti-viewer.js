/* Keep supplied viewer folders unchanged. Inline viewers load only when their
   native Reveal fragment appears, then retain state for return visits. */
window.RevealRTIViewer = {
  id: 'rupe-rti-viewer',
  init(reveal) {
    const frames = [...document.querySelectorAll('[data-rti-frame]')];
    const activate = slide => {
      frames.forEach(frame => {
        const section = frame.closest('section');
        const overlay = frame.closest('[data-rti-overlay]');
        const visible = section === slide && (!overlay || overlay.classList.contains('visible'));
        frame.inert = !visible;
        frame.tabIndex = visible ? 0 : -1;
        if (!visible) {
          if (document.activeElement === frame) {
            frame.blur();
            if (section === slide) {
              section.setAttribute('tabindex', '-1');
              section.focus({ preventScroll: true });
            }
          }
          return;
        }
        if (!frame.hasAttribute('src')) frame.setAttribute('src', frame.dataset.rtiSrc);
      });
    };
    frames.forEach(frame => {
      frame.addEventListener('load', () => {
        // Remote viewers retain their own controls and language. Browser origin
        // rules prevent the local deck from installing handlers inside them.
        let viewerDocument;
        try {
          viewerDocument = frame.contentDocument;
        } catch (error) {
          if (error.name === 'SecurityError') return;
          throw error;
        }
        if (!viewerDocument) return;
        viewerDocument.documentElement.lang = 'en-GB';
        viewerDocument.addEventListener('keydown', event => {
          if (event.key !== 'Escape') return;
          // Preserve the supplied viewer's own Escape action for open panels.
          // A subsequent Escape can then return to slide navigation.
          if (viewerDocument.querySelector?.('#help-panel.open, #mode-bar.open, #annotation-panel[aria-hidden="false"]')) return;
          event.preventDefault();
          event.stopPropagation();
          frame.blur();
          const slide = frame.closest('section');
          slide.setAttribute('tabindex', '-1');
          slide.focus({ preventScroll: true });
        }, true);
      });
    });
    reveal.on('ready', event => activate(event.currentSlide));
    reveal.on('slidechanged', event => activate(event.currentSlide));
    reveal.on('fragmentshown', () => activate(reveal.getCurrentSlide()));
    reveal.on('fragmenthidden', () => activate(reveal.getCurrentSlide()));
    activate(reveal.getCurrentSlide());
  }
};
