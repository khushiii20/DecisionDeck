/**
 * DecisionDeck - Authentication Handlers
 * Handles registration and login form submissions, client-side validation,
 * error banners, loading indicators, and session initialization.
 */

document.addEventListener('DOMContentLoaded', () => {
  // If user is already logged in and lands on login/register, direct to dashboard
  if (getToken()) {
    apiRequest('/auth/me').then(res => {
      if (res.ok) {
        window.location.href = '/dashboard.html';
      }
    });
  }

  // Check URL parameters for session expiry
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('expired') === '1') {
    const alertEl = document.getElementById('loginAlert');
    if (alertEl) {
      alertEl.className = 'alert alert-warning';
      alertEl.textContent = 'Your session has expired. Please log in again to continue.';
      alertEl.style.display = 'block';
    }
  }

  // ----------------- LOGIN FORM -----------------
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const emailInput = document.getElementById('email');
      const passwordInput = document.getElementById('password');
      const emailError = document.getElementById('emailError');
      const passwordError = document.getElementById('passwordError');
      const alertEl = document.getElementById('loginAlert');
      const submitBtn = document.getElementById('loginSubmitBtn');

      // Reset errors
      emailError.classList.remove('visible');
      passwordError.classList.remove('visible');
      alertEl.style.display = 'none';

      const email = emailInput.value.trim();
      const password = passwordInput.value;

      let hasError = false;
      if (!email || !email.includes('@')) {
        emailError.classList.add('visible');
        hasError = true;
      }
      if (!password) {
        passwordError.classList.add('visible');
        hasError = true;
      }

      if (hasError) return;

      // Loading state
      submitBtn.disabled = true;
      const originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = '<span class="spinner"></span> Logging in...';

      try {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
          setToken(data.access_token);
          setCurrentUser(data.user);
          window.location.href = '/dashboard.html';
        } else {
          alertEl.className = 'alert alert-danger';
          alertEl.textContent = data.detail || 'Invalid email or password.';
          alertEl.style.display = 'block';
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalText;
        }
      } catch (err) {
        alertEl.className = 'alert alert-danger';
        alertEl.textContent = 'Unable to connect to server. Please try again.';
        alertEl.style.display = 'block';
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    });
  }

  // ----------------- REGISTRATION FORM -----------------
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const emailInput = document.getElementById('regEmail');
      const passwordInput = document.getElementById('regPassword');
      const confirmInput = document.getElementById('regPasswordConfirm');
      const emailError = document.getElementById('regEmailError');
      const passwordError = document.getElementById('regPasswordError');
      const confirmError = document.getElementById('regConfirmError');
      const alertEl = document.getElementById('registerAlert');
      const submitBtn = document.getElementById('regSubmitBtn');

      // Reset errors
      emailError.classList.remove('visible');
      passwordError.classList.remove('visible');
      confirmError.classList.remove('visible');
      alertEl.style.display = 'none';

      const email = emailInput.value.trim();
      const password = passwordInput.value;
      const confirmPassword = confirmInput.value;

      let hasError = false;
      if (!email || !email.includes('@')) {
        emailError.classList.add('visible');
        hasError = true;
      }
      if (!password || password.length < 8) {
        passwordError.classList.add('visible');
        hasError = true;
      }
      if (password !== confirmPassword) {
        confirmError.classList.add('visible');
        hasError = true;
      }

      if (hasError) return;

      // Loading state
      submitBtn.disabled = true;
      const originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = '<span class="spinner"></span> Creating account...';

      try {
        const response = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
          setToken(data.access_token);
          setCurrentUser(data.user);
          window.location.href = '/dashboard.html';
        } else {
          alertEl.className = 'alert alert-danger';
          alertEl.textContent = data.detail || 'Registration failed. Please check inputs.';
          alertEl.style.display = 'block';
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalText;
        }
      } catch (err) {
        alertEl.className = 'alert alert-danger';
        alertEl.textContent = 'Unable to connect to server. Please try again.';
        alertEl.style.display = 'block';
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    });
  }
});
