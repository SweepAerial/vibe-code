/* ============================================
   SWEEP AERIAL PHOTOGRAPHY - Portal JS
   ============================================ */

/* ── Theme Toggle ── */
(function () {
  const CYCLE = ['dark', 'light', 'system'];
  const ICONS = {
    dark: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
    light: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
    system: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>'
  };
  const LABELS = { dark: 'Dark mode', light: 'Light mode', system: 'System default' };

  function applyTheme(pref) {
    const resolved = pref === 'system'
      ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : pref;
    document.documentElement.setAttribute('data-theme', resolved);
    const favicon = document.getElementById('favicon');
    if (favicon) favicon.href = resolved === 'light' ? 'images/PyramidBlack.svg' : 'images/PyramidWhite.svg';
    document.querySelectorAll('.theme-logo').forEach(img => {
      if (img.classList.contains('theme-logo--sap')) {
        img.src = resolved === 'light' ? 'images/SAPBlack.svg' : 'images/SAPWhite.svg';
      } else {
        img.src = resolved === 'light' ? 'images/FullSweepLogoBlackOutline.svg' : 'images/FullSweepLogoWhiteOutline.svg';
      }
    });
  }

  let pref = localStorage.getItem('theme') || 'dark';
  applyTheme(pref);

  const btn = document.getElementById('themeToggle');
  if (btn) {
    btn.innerHTML = ICONS[pref];
    btn.title = LABELS[pref];
    btn.addEventListener('click', () => {
      pref = CYCLE[(CYCLE.indexOf(pref) + 1) % CYCLE.length];
      localStorage.setItem('theme', pref);
      applyTheme(pref);
      btn.innerHTML = ICONS[pref];
      btn.title = LABELS[pref];
    });
  }

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (pref === 'system') applyTheme('system');
  });
})();

const DEMO_CREDENTIALS = {};

const SESSION_KEY = 'sweep_portal_session';

function getSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function setSession(user) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem(SESSION_KEY);
}

/* ── Login Page ── */
const loginForm = document.getElementById('portalLoginForm');
if (loginForm) {
  if (getSession()) {
    window.location.href = 'portal-dashboard.html';
  }

  loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = document.getElementById('portalEmail').value.trim().toLowerCase();
    const password = document.getElementById('portalPassword').value;
    const errorEl = document.getElementById('portalError');
    const submitBtn = loginForm.querySelector('button[type="submit"]');

    errorEl.style.display = 'none';
    submitBtn.textContent = 'Signing in...';
    submitBtn.disabled = true;

    setTimeout(() => {
      const cred = DEMO_CREDENTIALS[email];
      if (cred && cred.password === password) {
        setSession({ email, name: cred.name, company: cred.company, initials: cred.initials });
        window.location.href = 'portal-dashboard.html';
      } else {
        errorEl.style.display = 'block';
        errorEl.textContent = 'Invalid email or password. Please try again.';
        submitBtn.textContent = 'Sign In';
        submitBtn.disabled = false;
      }
    }, 800);
  });
}

/* ── Dashboard Page ── */
const dashboardEl = document.querySelector('.dashboard');
if (dashboardEl) {
  const session = getSession();
  if (!session) {
    window.location.href = 'portal.html';
  } else {
    const nameEls = document.querySelectorAll('[data-user-name]');
    const companyEls = document.querySelectorAll('[data-user-company]');
    const initialsEls = document.querySelectorAll('[data-user-initials]');

    nameEls.forEach(el => el.textContent = session.name);
    companyEls.forEach(el => el.textContent = session.company);
    initialsEls.forEach(el => el.textContent = session.initials);

    const logoutBtn = document.getElementById('logoutBtn');
    logoutBtn?.addEventListener('click', () => {
      clearSession();
      window.location.href = 'portal.html';
    });

    document.querySelectorAll('.deliverable-item__download').forEach(btn => {
      btn.addEventListener('click', () => {
        const name = btn.closest('.deliverable-item')?.querySelector('.deliverable-item__name')?.textContent;
        alert(`Download initiated: ${name}\n\nIn production, this would download the actual file from secure storage.`);
      });
    });
  }
}
