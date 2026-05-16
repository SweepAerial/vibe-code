/* ============================================
   SWEEP AERIAL PHOTOGRAPHY - Portal JS
   ============================================ */

const DEMO_CREDENTIALS = {
  'demo@sweep.com': { password: 'sweep2024', name: 'Demo Client', company: 'Demo Corp', initials: 'DC' },
  'client@example.com': { password: 'client123', name: 'Jane Smith', company: 'BuildRight Construction', initials: 'JS' }
};

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
