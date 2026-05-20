/* ============================================
   SWEEP AERIAL - Comparison Slider
   ============================================ */
(function () {
  document.querySelectorAll('.cslider').forEach(function (el) {
    var handle = el.querySelector('.cslider__handle');
    var split  = parseFloat(el.dataset.split || 50);
    var active = false;

    function update(pct) {
      split = Math.max(0, Math.min(100, pct));
      el.style.setProperty('--split', split + '%');
      handle.setAttribute('aria-valuenow', Math.round(split));
    }

    function posFromEvent(e) {
      var clientX = e.touches ? e.touches[0].clientX : e.clientX;
      var r = el.getBoundingClientRect();
      return (clientX - r.left) / r.width * 100;
    }

    /* Start drag from handle or anywhere on the slider */
    function startDrag(e) {
      e.preventDefault();
      active = true;
    }

    handle.addEventListener('mousedown', startDrag);
    handle.addEventListener('touchstart', startDrag, { passive: false });

    el.addEventListener('mousedown', function (e) {
      if (!handle.contains(e.target)) {
        active = true;
        update(posFromEvent(e));
      }
    });

    /* Move */
    window.addEventListener('mousemove', function (e) {
      if (active) update(posFromEvent(e));
    });

    window.addEventListener('touchmove', function (e) {
      if (!active) return;
      e.preventDefault();
      update(posFromEvent(e));
    }, { passive: false });

    /* End */
    window.addEventListener('mouseup',  function () { active = false; });
    window.addEventListener('touchend', function () { active = false; });

    /* Keyboard */
    handle.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft')  update(split - 2);
      if (e.key === 'ArrowRight') update(split + 2);
    });

    update(split);
  });
})();
