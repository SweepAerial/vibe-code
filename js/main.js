/* ============================================
   SWEEP AERIAL PHOTOGRAPHY - Main JS
   ============================================ */

/* ── Navbar ── */
const navbar = document.querySelector('.navbar');
const hamburger = document.querySelector('.navbar__hamburger');
const mobileNav = document.querySelector('.nav-mobile');

window.addEventListener('scroll', () => {
  if (window.scrollY > 20) {
    navbar?.classList.add('scrolled');
  } else {
    navbar?.classList.remove('scrolled');
  }
});

hamburger?.addEventListener('click', () => {
  hamburger.classList.toggle('open');
  mobileNav?.classList.toggle('open');
});

mobileNav?.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => {
    hamburger?.classList.remove('open');
    mobileNav.classList.remove('open');
  });
});

/* ── Active nav link ── */
const currentPath = window.location.pathname.split('/').pop() || 'index.html';
document.querySelectorAll('.navbar__links a, .nav-mobile a').forEach(link => {
  const href = link.getAttribute('href');
  if (href === currentPath || (currentPath === '' && href === 'index.html')) {
    link.classList.add('active');
  }
});

/* ── Intersection Observer - Fade In ── */
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));

/* ── Carousel ── */
class Carousel {
  constructor(el) {
    this.el = el;
    this.track = el.querySelector('.carousel__track');
    this.slides = el.querySelectorAll('.carousel__slide');
    this.dots = el.querySelectorAll('.carousel__dot');
    this.prevBtn = el.querySelector('.carousel__btn--prev');
    this.nextBtn = el.querySelector('.carousel__btn--next');
    this.progress = el.querySelector('.carousel__progress');
    this.current = 0;
    this.total = this.slides.length;
    this.interval = null;
    this.init();
  }

  init() {
    this.prevBtn?.addEventListener('click', () => { this.prev(); this.resetInterval(); });
    this.nextBtn?.addEventListener('click', () => { this.next(); this.resetInterval(); });
    this.dots.forEach((dot, i) => {
      dot.addEventListener('click', () => { this.goTo(i); this.resetInterval(); });
    });
    this.update();
    this.startInterval();
  }

  goTo(index) {
    this.current = (index + this.total) % this.total;
    this.update();
  }

  next() { this.goTo(this.current + 1); }
  prev() { this.goTo(this.current - 1); }

  update() {
    if (this.track) {
      this.track.style.transform = `translateX(-${this.current * 100}%)`;
    }
    this.dots.forEach((dot, i) => {
      dot.classList.toggle('active', i === this.current);
    });
    if (this.progress) {
      this.progress.textContent = `${this.current + 1} / ${this.total}`;
    }
  }

  startInterval() {
    this.interval = setInterval(() => this.next(), 5000);
  }

  resetInterval() {
    clearInterval(this.interval);
    this.startInterval();
  }
}

document.querySelectorAll('.carousel').forEach(el => new Carousel(el));

/* ── Portfolio Filter ── */
const filterBtns = document.querySelectorAll('.filter-btn');
const portfolioItems = document.querySelectorAll('.portfolio-item');

filterBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    filterBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const filter = btn.dataset.filter;
    portfolioItems.forEach(item => {
      if (filter === 'all' || item.dataset.category === filter) {
        item.style.display = '';
        setTimeout(() => item.style.opacity = '1', 10);
      } else {
        item.style.opacity = '0';
        setTimeout(() => item.style.display = 'none', 300);
      }
    });
  });
});

/* ── Contact Form ── */
const contactForm = document.getElementById('contactForm');
const formSuccess = document.querySelector('.form-success');

contactForm?.addEventListener('submit', (e) => {
  e.preventDefault();
  const name = document.getElementById('name')?.value;
  const email = document.getElementById('email')?.value;
  const company = document.getElementById('company')?.value;
  const service = document.getElementById('service')?.value;
  const message = document.getElementById('message')?.value;

  const subject = `Sweep Aerial Enquiry - ${service || 'General'} - ${company || name}`;
  const body = `Name: ${name}\nEmail: ${email}\nCompany: ${company}\nService: ${service}\n\n${message}`;
  const mailtoLink = `mailto:info@sweepaerialphotography.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;

  window.location.href = mailtoLink;

  if (formSuccess) {
    contactForm.style.display = 'none';
    formSuccess.style.display = 'block';
  }
});

/* ── Counter animation ── */
function animateCounter(el) {
  const target = parseInt(el.dataset.target, 10);
  const suffix = el.dataset.suffix || '';
  const duration = 1500;
  const start = performance.now();

  function step(timestamp) {
    const progress = Math.min((timestamp - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.floor(eased * target) + suffix;
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

const counterObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting && !entry.target.dataset.animated) {
      entry.target.dataset.animated = 'true';
      animateCounter(entry.target);
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll('.stats__number[data-target]').forEach(el => counterObserver.observe(el));
