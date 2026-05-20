/* ============================================
   SWEEP AERIAL - Comparison Slider
   ============================================ */
(function () {

  /* ── Embedded Slider ── */
  class EmbeddedSlider {
    constructor(el) {
      this.el = el;
      this.handle = el.querySelector('.cslider__handle');
      this.dragging = false;
      this.split = parseFloat(el.dataset.split || 50);
      this.bind();
      this.update(this.split);
    }

    bind() {
      const onStart = e => {
        e.preventDefault();
        this.dragging = true;
      };
      const onEnd = () => { this.dragging = false; };
      const onMove = e => {
        if (!this.dragging) return;
        const x = e.touches ? e.touches[0].clientX : e.clientX;
        const r = this.el.getBoundingClientRect();
        this.update(Math.max(0, Math.min(100, (x - r.left) / r.width * 100)));
      };

      this.handle.addEventListener('mousedown', onStart);
      this.handle.addEventListener('touchstart', onStart, { passive: false });
      window.addEventListener('mousemove', onMove);
      window.addEventListener('touchmove', onMove, { passive: true });
      window.addEventListener('mouseup', onEnd);
      window.addEventListener('touchend', onEnd);

      this.el.addEventListener('mousedown', e => {
        if (this.handle.contains(e.target)) return;
        if (e.target.closest('.cslider__expand')) return;
        onStart(e);
        onMove(e);
      });

      this.handle.addEventListener('keydown', e => {
        if (e.key === 'ArrowLeft') this.update(Math.max(0, this.split - 2));
        if (e.key === 'ArrowRight') this.update(Math.min(100, this.split + 2));
      });

      const expandBtn = this.el.querySelector('.cslider__expand');
      if (expandBtn) {
        expandBtn.addEventListener('click', e => {
          e.stopPropagation();
          const imgA = this.el.querySelector('.cslider__img--a');
          const imgB = this.el.querySelector('.cslider__img--b');
          const labels = this.el.querySelectorAll('.cslider__label');
          openLightbox(imgA.src, imgB.src, labels[0]?.textContent, labels[1]?.textContent, this.split);
        });
      }
    }

    update(pct) {
      this.split = pct;
      this.el.style.setProperty('--split', pct + '%');
      this.handle.setAttribute('aria-valuenow', Math.round(pct));
    }
  }

  /* ── Lightbox ── */
  let lightbox = null;

  function buildLightbox() {
    const el = document.createElement('div');
    el.className = 'cslider-lb';
    el.setAttribute('aria-hidden', 'true');
    /*
     * Two separate layers (layerA, layerB) each fill the viewport.
     * Both receive the same CSS transform so they move identically.
     * layerA is clipped by its own width (overflow:hidden) in viewport space —
     * this keeps the split line anchored to the viewport, not the image.
     */
    el.innerHTML = `
      <div class="cslider-lb__bar">
        <span class="cslider-lb__hint">Pinch to zoom &middot; Drag to pan &middot; Move divider to compare</span>
        <button class="cslider-lb__close" aria-label="Close">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <div class="cslider-lb__viewport">
        <div class="cslider-lb__layer cslider-lb__layer--b">
          <img class="cslider-lb__img" src="" alt="" draggable="false">
        </div>
        <div class="cslider-lb__layer cslider-lb__layer--a">
          <img class="cslider-lb__img" src="" alt="" draggable="false">
        </div>
        <div class="cslider-lb__handle">
          <div class="cslider__line"></div>
          <div class="cslider__grip">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="8 9 4 12 8 15"/><polyline points="16 9 20 12 16 15"/>
            </svg>
          </div>
        </div>
        <div class="cslider-lb__labels">
          <span class="cslider-lb__label cslider-lb__label--a"></span>
          <span class="cslider-lb__label cslider-lb__label--b"></span>
        </div>
        <div class="cslider-lb__zoom-btns">
          <button class="cslider-lb__zoom-btn" data-zoom="in" aria-label="Zoom in">+</button>
          <button class="cslider-lb__zoom-btn" data-zoom="out" aria-label="Zoom out">−</button>
          <button class="cslider-lb__zoom-btn" data-zoom="reset" aria-label="Reset zoom" style="font-size:0.7rem;">↺</button>
        </div>
      </div>
    `;
    document.body.appendChild(el);

    const viewport  = el.querySelector('.cslider-lb__viewport');
    const layerA    = el.querySelector('.cslider-lb__layer--a');
    const layerB    = el.querySelector('.cslider-lb__layer--b');
    const imgA      = layerA.querySelector('.cslider-lb__img');
    const imgB      = layerB.querySelector('.cslider-lb__img');
    const handle    = el.querySelector('.cslider-lb__handle');
    const labelA    = el.querySelector('.cslider-lb__label--a');
    const labelB    = el.querySelector('.cslider-lb__label--b');

    const MIN_SCALE = 0.5, MAX_SCALE = 20;
    let scale = 1, tx = 0, ty = 0;
    let split = 0.5; // fraction of viewport width (0–1)
    let isDraggingHandle = false, isDraggingCanvas = false;
    let lastX = 0, lastY = 0;
    let lastTouchDist = 0, lastMidX = 0, lastMidY = 0;

    function applyTransform() {
      const t = `translate(${tx}px,${ty}px) scale(${scale})`;
      layerA.style.transform = t;
      layerB.style.transform = t;
    }

    function applySplit() {
      const vw = viewport.clientWidth;
      const px = split * vw;
      handle.style.left = px + 'px';
      /* layerA is clipped by its own width in viewport space.
         Both layers share the same transform, so the images line up exactly.
         The clip is controlled by layerA's width — no clip-path math needed. */
      layerA.style.width = px + 'px';
    }

    function zoomTo(newScale, pivotX, pivotY) {
      newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, newScale));
      tx = pivotX - (pivotX - tx) * (newScale / scale);
      ty = pivotY - (pivotY - ty) * (newScale / scale);
      scale = newScale;
      applyTransform();
    }

    /* Wheel zoom */
    viewport.addEventListener('wheel', e => {
      e.preventDefault();
      const r = viewport.getBoundingClientRect();
      zoomTo(scale * (e.deltaY < 0 ? 1.12 : 0.9), e.clientX - r.left, e.clientY - r.top);
    }, { passive: false });

    /* Mouse */
    viewport.addEventListener('mousedown', e => {
      const hRect = handle.getBoundingClientRect();
      const near  = e.clientX >= hRect.left - 20 && e.clientX <= hRect.right + 20;
      if (near) {
        isDraggingHandle = true;
      } else {
        isDraggingCanvas = true;
        viewport.style.cursor = 'grabbing';
      }
      lastX = e.clientX;
      lastY = e.clientY;
      e.preventDefault();
    });

    window.addEventListener('mousemove', e => {
      if (isDraggingHandle) {
        const r = viewport.getBoundingClientRect();
        split = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width));
        applySplit();
      } else if (isDraggingCanvas) {
        tx += e.clientX - lastX;
        ty += e.clientY - lastY;
        lastX = e.clientX;
        lastY = e.clientY;
        applyTransform();
      }
    });

    window.addEventListener('mouseup', () => {
      isDraggingHandle = false;
      isDraggingCanvas = false;
      viewport.style.cursor = '';
    });

    /* Touch */
    viewport.addEventListener('touchstart', e => {
      e.preventDefault();
      if (e.touches.length === 1) {
        const touch = e.touches[0];
        const hRect = handle.getBoundingClientRect();
        const near  = touch.clientX >= hRect.left - 32 && touch.clientX <= hRect.right + 32;
        isDraggingHandle = near;
        isDraggingCanvas = !near;
        lastX = touch.clientX;
        lastY = touch.clientY;
      } else if (e.touches.length === 2) {
        isDraggingHandle = false;
        isDraggingCanvas = false;
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        lastTouchDist = Math.hypot(dx, dy);
        const r = viewport.getBoundingClientRect();
        lastMidX = (e.touches[0].clientX + e.touches[1].clientX) / 2 - r.left;
        lastMidY = (e.touches[0].clientY + e.touches[1].clientY) / 2 - r.top;
      }
    }, { passive: false });

    viewport.addEventListener('touchmove', e => {
      e.preventDefault();
      if (e.touches.length === 1) {
        const touch = e.touches[0];
        if (isDraggingHandle) {
          const r = viewport.getBoundingClientRect();
          split = Math.max(0, Math.min(1, (touch.clientX - r.left) / r.width));
          applySplit();
        } else if (isDraggingCanvas) {
          tx += touch.clientX - lastX;
          ty += touch.clientY - lastY;
          lastX = touch.clientX;
          lastY = touch.clientY;
          applyTransform();
        }
      } else if (e.touches.length === 2) {
        const dx   = e.touches[0].clientX - e.touches[1].clientX;
        const dy   = e.touches[0].clientY - e.touches[1].clientY;
        const dist = Math.hypot(dx, dy);
        const r    = viewport.getBoundingClientRect();
        const midX = (e.touches[0].clientX + e.touches[1].clientX) / 2 - r.left;
        const midY = (e.touches[0].clientY + e.touches[1].clientY) / 2 - r.top;

        /* One formula handles both zoom-to-midpoint AND pan-with-midpoint */
        const factor   = dist / lastTouchDist;
        const newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, scale * factor));
        tx = midX - (lastMidX - tx) * (newScale / scale);
        ty = midY - (lastMidY - ty) * (newScale / scale);
        scale = newScale;

        lastTouchDist = dist;
        lastMidX = midX;
        lastMidY = midY;
        applyTransform();
      }
    }, { passive: false });

    viewport.addEventListener('touchend', e => {
      if (e.touches.length === 0) {
        isDraggingHandle = false;
        isDraggingCanvas = false;
      } else if (e.touches.length === 1) {
        /* One finger lifted during pinch — resume single-finger tracking */
        isDraggingCanvas = true;
        lastX = e.touches[0].clientX;
        lastY = e.touches[0].clientY;
      }
    });

    /* Zoom buttons */
    el.querySelectorAll('.cslider-lb__zoom-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const cx = viewport.clientWidth / 2;
        const cy = viewport.clientHeight / 2;
        if (btn.dataset.zoom === 'in')    zoomTo(scale * 1.5, cx, cy);
        else if (btn.dataset.zoom === 'out') zoomTo(scale / 1.5, cx, cy);
        else { scale = 1; tx = 0; ty = 0; applyTransform(); }
      });
    });

    /* Close */
    function close() {
      el.classList.remove('open');
      el.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    }
    el.querySelector('.cslider-lb__close').addEventListener('click', close);
    el.addEventListener('click', e => { if (e.target === el) close(); });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && el.classList.contains('open')) close();
    });

    return {
      open(srcA, srcB, lA, lB, initialSplit) {
        imgA.src = srcA;
        imgB.src = srcB;
        labelA.textContent = lA || 'Before';
        labelB.textContent = lB || 'After';
        scale = 1; tx = 0; ty = 0;
        split = Math.max(0, Math.min(1, (initialSplit || 50) / 100));
        el.setAttribute('aria-hidden', 'false');
        el.classList.add('open');
        document.body.style.overflow = 'hidden';
        requestAnimationFrame(() => { applyTransform(); applySplit(); });
      }
    };
  }

  function openLightbox(srcA, srcB, lA, lB, split) {
    if (!lightbox) lightbox = buildLightbox();
    lightbox.open(srcA, srcB, lA, lB, split);
  }

  /* Init */
  document.querySelectorAll('.cslider').forEach(el => new EmbeddedSlider(el));

})();
