/**
 * DecisionDeck - Dashboard Script
 * Manages decision listings, live search, template initialization,
 * and deletion confirmation modal.
 */

let allDecisions = [];
let pendingDeleteId = null;

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Authenticate user
  const user = await checkAuth();
  if (!user) return;

  const userGreeting = document.getElementById('userGreeting');
  if (userGreeting) {
    userGreeting.textContent = user.email;
  }

  // 2. Setup logout
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      try {
        await apiRequest('/auth/logout', { method: 'POST' });
      } catch (e) {
        // proceed regardless
      }
      clearSession();
      window.location.href = '/login.html';
    });
  }

  // 3. Load decisions
  await loadDecisions();

  // 4. Setup search input
  const searchInput = document.getElementById('decisionSearchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      const filtered = allDecisions.filter(d => 
        d.title.toLowerCase().includes(query) || 
        (d.description && d.description.toLowerCase().includes(query))
      );
      renderDecisionsList(filtered);
    });
  }

  // 5. Setup Template Modal
  setupTemplateModal();

  // 6. Setup Delete Modal
  setupDeleteModal();
});

// Fetch decisions from backend
async function loadDecisions() {
  const container = document.getElementById('decisionsContainer');
  try {
    const res = await apiRequest('/decisions');
    if (!res.ok) {
      container.innerHTML = `
        <div class="alert alert-danger">
          Failed to load decisions. <button class="btn btn-sm btn-outline" onclick="loadDecisions()">Retry</button>
        </div>
      `;
      return;
    }

    allDecisions = await res.json();
    renderDecisionsList(allDecisions);
  } catch (err) {
    container.innerHTML = `
      <div class="alert alert-danger">
        Network error loading decisions. Please verify the server is running.
      </div>
    `;
  }
}

// Render decisions into grid or show empty state
function renderDecisionsList(decisions) {
  const container = document.getElementById('decisionsContainer');
  const countBadge = document.getElementById('decisionCountBadge');

  if (countBadge) {
    countBadge.textContent = `${decisions.length} ${decisions.length === 1 ? 'decision' : 'decisions'}`;
  }

  if (decisions.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom: var(--space-md); color: var(--text-secondary);">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="9" y1="3" x2="9" y2="21"></line>
          <line x1="15" y1="3" x2="15" y2="21"></line>
        </svg>
        <h2 style="font-size: 1.3rem; margin-bottom: var(--space-xs);">No Decisions Found</h2>
        <p style="margin-bottom: var(--space-lg); max-width: 480px; margin-left: auto; margin-right: auto;">
          Start by comparing career offers, tech hardware, or project choices with weighted priorities.
        </p>
        <div class="flex justify-center gap-sm">
          <button onclick="document.getElementById('openTemplateModalBtn').click()" class="btn btn-secondary">
            Use a Template
          </button>
          <a href="/decision.html" class="btn btn-primary">
            Create Blank Decision
          </a>
        </div>
      </div>
    `;
    return;
  }

  const gridHtml = `
    <div class="decision-grid">
      ${decisions.map(d => `
        <div class="card card-interactive decision-card" id="decCard_${d.id}">
          <div>
            <div class="card-header">
              <h2 class="card-title" style="font-size: 1.2rem; word-break: break-word;">${escapeHtml(d.title)}</h2>
              <p class="card-subtitle" style="font-size: 0.85rem; line-height: 1.4; word-break: break-word;">
                ${d.description ? escapeHtml(d.description) : 'No description provided.'}
              </p>
            </div>

            <div class="decision-meta">
              <div class="meta-tag">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                  <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
                </svg>
                <span>${d.options_count} Alternatives</span>
              </div>
              <div class="meta-tag">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 3v18M3 9l9-6 9 6M3 9l3 6M21 9l-3 6"></path>
                </svg>
                <span>${d.criteria_count} Criteria</span>
              </div>
            </div>
          </div>

          <div style="border-top: 1px solid var(--border-color); padding-top: var(--space-md); margin-top: var(--space-md); display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 0.75rem; color: var(--text-muted);">
              Updated ${formatDate(d.updated_at)}
            </span>
            <div class="flex gap-xs">
              <button onclick="promptDelete('${d.id}', '${escapeHtml(d.title.replace(/'/g, "\\'"))}')" class="btn btn-sm btn-danger" aria-label="Delete decision">
                Delete
              </button>
              <a href="/decision.html?id=${d.id}" class="btn btn-sm btn-primary">
                Open Workspace &rarr;
              </a>
            </div>
          </div>
        </div>
      `).join('')}
    </div>
  `;

  container.innerHTML = gridHtml;
}

// Template selection modal
function setupTemplateModal() {
  const modal = document.getElementById('templateModal');
  const openBtn = document.getElementById('openTemplateModalBtn');
  const listEl = document.getElementById('templatesList');

  if (!modal || !openBtn || !listEl) return;

  // Render templates from DECISION_TEMPLATES
  listEl.innerHTML = DECISION_TEMPLATES.map(t => `
    <div class="template-item" onclick="createFromTemplate('${t.id}')">
      <div class="flex items-center justify-between" style="margin-bottom: 0.25rem;">
        <strong style="color: var(--text-primary); font-size: 1rem;">${t.title}</strong>
        <span class="badge badge-purple">${t.badge}</span>
      </div>
      <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.5rem;">${t.description}</p>
      <div style="font-size: 0.775rem; color: var(--text-muted);">
        Includes ${t.options.length} alternatives, ${t.criteria.length} criteria with weights totaling 100%
      </div>
    </div>
  `).join('');

  openBtn.addEventListener('click', () => {
    modal.classList.add('active');
  });

  modal.querySelectorAll('.close-modal').forEach(btn => {
    btn.addEventListener('click', () => modal.classList.remove('active'));
  });

  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('active');
  });
}

// Create decision from template
async function createFromTemplate(templateId) {
  const template = DECISION_TEMPLATES.find(t => t.id === templateId);
  if (!template) return;

  const modal = document.getElementById('templateModal');
  if (modal) modal.classList.remove('active');

  showToast('Creating decision from template...', 'info');

  try {
    const payload = {
      title: template.title,
      description: template.description,
      options: template.options,
      criteria: template.criteria,
      ratings: template.ratings,
      constraints: template.constraints
    };

    const res = await apiRequest('/decisions', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const created = await res.json();
      showToast('Decision created! Redirecting to workspace...', 'success');
      setTimeout(() => {
        window.location.href = `/decision.html?id=${created.id}`;
      }, 500);
    } else {
      const err = await res.json();
      showToast(err.detail || 'Failed to initialize template.', 'error');
    }
  } catch (err) {
    showToast('Failed to create decision from template.', 'error');
  }
}

// Delete modal confirmation
function promptDelete(decisionId, title) {
  pendingDeleteId = decisionId;
  const modal = document.getElementById('deleteModal');
  const textEl = document.getElementById('deleteModalText');
  if (textEl) {
    textEl.innerHTML = `Are you sure you want to permanently delete <strong>"${title}"</strong>? All options, criteria, and scores will be removed.`;
  }
  if (modal) {
    modal.classList.add('active');
  }
}

function setupDeleteModal() {
  const modal = document.getElementById('deleteModal');
  const confirmBtn = document.getElementById('confirmDeleteBtn');
  if (!modal || !confirmBtn) return;

  modal.querySelectorAll('.close-modal').forEach(btn => {
    btn.addEventListener('click', () => {
      modal.classList.remove('active');
      pendingDeleteId = null;
    });
  });

  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.classList.remove('active');
      pendingDeleteId = null;
    }
  });

  confirmBtn.addEventListener('click', async () => {
    if (!pendingDeleteId) return;

    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<span class="spinner"></span> Deleting...';

    try {
      const res = await apiRequest(`/decisions/${pendingDeleteId}`, { method: 'DELETE' });
      if (res.ok || res.status === 204) {
        showToast('Decision deleted successfully.', 'success');
        modal.classList.remove('active');
        allDecisions = allDecisions.filter(d => d.id !== pendingDeleteId);
        renderDecisionsList(allDecisions);
      } else {
        showToast('Failed to delete decision.', 'error');
      }
    } catch (err) {
      showToast('Error deleting decision.', 'error');
    } finally {
      confirmBtn.disabled = false;
      confirmBtn.innerHTML = 'Delete Permanently';
      pendingDeleteId = null;
    }
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
