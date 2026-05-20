/* ============================================
   SWEEP AERIAL - Comparison Slider
   ============================================ */
(function () {

  /* ── Embedded Slider ── */
  class EmbeddedSlider {
    constructor(el) {
      this.el = el;
      this.handle = el.querySelector('.cslider__handle');
      this.imgA = el.querySelector('.cslider__img--a');
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
    el.innerHTML = `
      <div class="cslider-lb__bar">
        <span class="cslider-lb__hint">Scroll to zoom &middot; Drag to pan &middot; Move divider to compare</span>
        <button class="cslider-lb__close" aria-label="Close">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <div class="cslider-lb__viewport">
        <div class="cslider-lb__canvas">
          <img class="cslider-lb__img cslider-lb__img--b" src="" alt="" draggable="false">
          <img class="cslider-lb__img cslider-lb__img--a" src="" alt="" draggable="false">
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

    const viewport = el.querySelector('.cslider-lb__viewport');
    const canvas = el.querySelector('.cslider-lb__canvas');
    const imgA = canvas.querySelector('.cslider-lb__img--a');
    const imgB = canvas.querySelector('.cslider-lb__img--b');
    const handle = el.querySelector('.cslider-lb__handle');
    const labelA = el.querySelector('.cslider-lb__label--a');
    const labelB = el.querySelector('.cslider-lb__label--b');

    const MIN_SCALE = 0.8, MAX_SCALE = 20;
    let scale = 1, tx = 0, ty = 0;
    let split = 0.5;
    let isDraggingHandle = false, isDraggingCanvas = false;
    let lastX = 0, lastY = 0;

    function applyTransform() {
      canvas.style.transform = `translate(${tx}px,${ty}px) scale(${scale})`;
      refreshClip();
    }

    function refreshHandle() {
      const vw = viewport.clientWidth;
      handle.style.left = (split * vw) + 'px';
      refreshClip();
    }

    function refreshClip() {
      const vw = viewport.clientWidth;
      const handleX = split * vw;
      const fracInCanvas = (handleX - tx) / (vw * scale);
      const clamped = Math.max(0, Math.min(1, fracInCanvas));
      imgA.style.clipPath = `inset(0 ${((1 - clamped) * 100).toFixed(2)}% 0 0)`;
    }

    function zoomTo(newScale, pivotX, pivotY) {
      newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, newScale));
      tx = pivotX - (pivotX - tx) * (newScale / scale);
      ty = pivotY - (pivotY - ty) * (newScale / scale);
      scale = newScale;
      applyTransform();
    }

    function constrainPan() {
      const vw = viewport.clientWidth;
      const vh = viewport.clientHeight;
      const cw = vw * scale;
      const ch = vh * scale;
      const margin = 80;
      tx = Math.max(-(cw - margin), Math.min(vw - margin, tx));
      ty = Math.max(-(ch - margin), Math.min(vh - margin, ty));
    }

    /* Wheel zoom */
    viewport.addEventListener('wheel', e => {
      e.preventDefault();
      const r = viewport.getBoundingClientRect();
      const px = e.clientX - r.left;
      const py = e.clientY - r.top;
      zoomTo(scale * (e.deltaY < 0 ? 1.12 : 0.9), px, py);
    }, { passive: false });

    /* Mouse drag */
    viewport.addEventListener('mousedown', e => {
      const hRect = handle.getBoundingClientRect();
      const near = e.clientX >= hRect.left - 18 && e.clientX <= hRect.right + 18;
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
        refreshHandle();
      } else if (isDraggingCanvas) {
        tx += e.clientX - lastX;
        ty += e.clientY - lastY;
        lastX = e.clientX;
        lastY = e.clientY;
        constrainPan();
        applyTransform();
      }
    });

    window.addEventListener('mouseup', () => {
      isDraggingHandle = false;
      isDraggingCanvas = false;
      viewport.style.cursor = '';
    });

    /* Touch */
    let lastTouchDist = 0, touchPivotX = 0, touchPivotY = 0;

    viewport.addEventListener('touchstart', e => {
      if (e.touches.length === 1) {
        const touch = e.touches[0];
        const r = viewport.getBoundingClientRect();
        const hRect = handle.getBoundingClientRect();
        const near = touch.clientX >= hRect.left - 28 && touch.clientX <= hRect.right + 28;
        if (near) {
          isDraggingHandle = true;
        } else {
          isDraggingCanvas = true;
        }
        lastX = touch.clientX;
        lastY = touch.clientY;
      } else if (e.touches.length === 2) {
        isDraggingHandle = false;
        isDraggingCanvas = false;
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        lastTouchDist = Math.hypot(dx, dy);
        const r = viewport.getBoundingClientRect();
        touchPivotX = (e.touches[0].clientX + e.touches[1].clientX) / 2 - r.left;
        touchPivotY = (e.touches[0].clientY + e.touches[1].clientY) / 2 - r.top;
      }
      e.preventDefault();
    }, { passive: false });

    viewport.addEventListener('touchmove', e => {
      if (e.touches.length === 1) {
        const touch = e.touches[0];
        if (isDraggingHandle) {
          const r = viewport.getBoundingClientRect();
          split = Math.max(0, Math.min(1, (touch.clientX - r.left) / r.width));
          refreshHandle();
        } else if (isDraggingCanvas) {
          tx += touch.clientX - lastX;
          ty += touch.clientY - lastY;
          lastX = touch.clientX;
          lastY = touch.clientY;
          constrainPan();
          applyTransform();
        }
      } else if (e.touches.length === 2) {
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        const dist = Math.hypot(dx, dy);
        zoomTo(scale * (dist / lastTouchDist), touchPivotX, touchPivotY);
        lastTouchDist = dist;
      }
      e.preventDefault();
    }, { passive: false });

    viewport.addEventListener('touchend', () => {
      isDraggingHandle = false;
      isDraggingCanvas = false;
    });

    /* Zoom buttons */
    el.querySelectorAll('.cslider-lb__zoom-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const vw = viewport.clientWidth;
        const vh = viewport.clientHeight;
        const cx = vw / 2, cy = vh / 2;
        if (btn.dataset.zoom === 'in') zoomTo(scale * 1.5, cx, cy);
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
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && el.classList.contains('open')) close(); });

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
        requestAnimationFrame(() => { applyTransform(); refreshHandle(); });
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
