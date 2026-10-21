/* Reveal 5.1 uses offsetLeft/offsetTop when center:false. Those coordinates
 * belong to different parents on the cover and analysis slide. Measure each
 * image in its slide's visual coordinate system instead, including deck scale.
 */
window.CervidTransition = (() => {
  function measure(element) {
    const image = element.getBoundingClientRect();
    const slide = element.closest('section').getBoundingClientRect();
    return {
      x: image.left - slide.left,
      y: image.top - slide.top,
      width: image.width,
      height: image.height
    };
  }

  function matcher(fromSlide, toSlide) {
    return this.getAutoAnimatePairs(fromSlide, toSlide).map(pair => {
      if (pair.from.dataset.id === 'cervid-source' &&
          pair.to.dataset.id === 'cervid-source') {
        return { ...pair, options: { ...pair.options, measure } };
      }
      return pair;
    });
  }

  return { matcher };
})();
