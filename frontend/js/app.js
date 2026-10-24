/**
 * DecisionDeck - Shared App Utilities & API Client
 * Clean vanilla JavaScript module for API interaction, session management,
 * accessible toasts, and UI helpers.
 */

const API_BASE = '/api';

// Session management
function getToken() {
  return localStorage.getItem('dd_token');
}

function setToken(token) {
  if (token) {
    localStorage.setItem('dd_token', token);
  } else {
    localStorage.removeItem('dd_token');
  }
}

function getCurrentUser() {
  const userJson = localStorage.getItem('dd_user');
  if (userJson) {
    try {
      return JSON.parse(userJson);
    } catch (e) {
      return null;
    }
  }
  return null;
}

function setCurrentUser(user) {
  if (user) {
    localStorage.setItem('dd_user', JSON.stringify(user));
  } else {
    localStorage.removeItem('dd_user');
  }
}

function clearSession() {
  localStorage.removeItem('dd_token');
  localStorage.removeItem('dd_user');
}

// Global Toast Notifications
function showToast(message, type = 'info', durationMs = 4000) {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = `
      position: fixed;
      bottom: 1.5rem;
      right: 1.5rem;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      max-width: 380px;
      pointer-events: none;
    `;
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `alert alert-${type === 'error' ? 'danger' : type}`;
  toast.style.cssText = `
    box-shadow: var(--shadow-lg);
    pointer-events: auto;
    margin-bottom: 0;
    transition: opacity 200ms ease, transform 200ms ease;
    opacity: 0;
    transform: translateY(10px);
  `;
  toast.setAttribute('role', 'alert');
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);

  // Trigger animation
  requestAnimationFrame(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
  });

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 250);
  }, durationMs);
}

// Authenticated API request helper
async function apiRequest(endpoint, options = {}) {
  const headers = options.headers || {};
  const token = getToken();

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers
    });

    // Check for expired session / unauthorized
    if (response.status === 401 && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/register')) {
      clearSession();
      if (!window.location.pathname.includes('/login.html') && !window.location.pathname.includes('/register.html') && window.location.pathname !== '/') {
        window.location.href = '/login.html?expired=1';
      }
    }

    return response;
  } catch (err) {
    console.error('API Network error:', err);
    showToast('Network error. Please check your internet connection or server status.', 'error');
    throw err;
  }
}

// Ensure auth check on protected pages
async function checkAuth(redirectIfUnauth = true) {
  const token = getToken();
  if (!token) {
    if (redirectIfUnauth) {
      window.location.href = '/login.html';
    }
    return null;
  }

  try {
    const res = await apiRequest('/auth/me');
    if (res.ok) {
      const user = await res.json();
      setCurrentUser(user);
      return user;
    } else {
      clearSession();
      if (redirectIfUnauth) {
        window.location.href = '/login.html';
      }
      return null;
    }
  } catch (e) {
    if (redirectIfUnauth) {
      window.location.href = '/login.html';
    }
    return null;
  }
}

// Format UTC date string to readable format
function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}
