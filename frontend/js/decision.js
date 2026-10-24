/**
 * DecisionDeck - Decision Workspace Script
 * Handles alternatives editor, criteria & weight validation, rating matrix,
 * hard requirements, calculation, What-if Simulator, charts, and CSV export.
 */

let decisionState = {
  id: null,
  title: '',
  description: '',
  options: [],
  criteria: [],
  ratings: {},     // key: `${optId}___${critId}` -> float
  constraints: [],
  savedCriteriaWeights: {} // baseline for simulator reset
};

let isSimulating = false;
let temporaryWeights = {};

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Authenticate
  const user = await checkAuth();
  if (!user) return;

  // 2. Parse ID from URL
  const urlParams = new URLSearchParams(window.location.search);
  const idFromUrl = urlParams.get('id');

  if (idFromUrl) {
    await loadExistingDecision(idFromUrl);
  } else {
    initializeBlankDecision();
  }

  // 3. Bind top action buttons
  document.getElementById('saveDecisionBtn').addEventListener('click', () => saveDecision(true));
  document.getElementById('calculateBtn').addEventListener('click', () => calculateResults());
  document.getElementById('exportCsvBtn').addEventListener('click', () => exportCsv());

  // 4. Bind sub-entity add buttons
  document.getElementById('addOptionBtn').addEventListener('click', () => addOption());
  document.getElementById('addCriterionBtn').addEventListener('click', () => addCriterion());
  document.getElementById('addConstraintBtn').addEventListener('click', () => addConstraint());
  document.getElementById('balanceWeightsBtn').addEventListener('click', () => autoBalanceWeights());
  document.getElementById('refreshMatrixBtn').addEventListener('click', () => renderMatrix());

  // 5. Bind simulator actions
  document.getElementById('resetSimulationBtn').addEventListener('click', () => resetSimulation());
  document.getElementById('applySimulationWeightsBtn').addEventListener('click', () => applySimulationWeights());

  // 6. Bind title/desc live update
  document.getElementById('decisionTitleInput').addEventListener('input', (e) => {
    decisionState.title = e.target.value;
    document.getElementById('decisionTitleHeading').textContent = e.target.value.trim() || 'New Decision';
    markUnsaved();
  });

  document.getElementById('decisionDescInput').addEventListener('input', (e) => {
    decisionState.description = e.target.value;
    markUnsaved();
  });
});

// Load decision from API
async function loadExistingDecision(id) {
  showWorkspaceAlert('Loading decision...', 'info');
  try {
    const res = await apiRequest(`/decisions/${id}`);
    if (!res.ok) {
      showWorkspaceAlert('Decision not found or you do not have permission to view it.', 'danger');
      return;
    }

    const data = await res.json();
    decisionState.id = data.id;
    decisionState.title = data.title;
    decisionState.description = data.description || '';
    decisionState.options = data.options || [];
    decisionState.criteria = data.criteria || [];
    decisionState.constraints = data.constraints || [];

    // Parse ratings map
    decisionState.ratings = {};
    if (data.ratings) {
      data.ratings.forEach(r => {
        decisionState.ratings[`${r.option_id}___${r.criterion_id}`] = r.rating;
      });
    }

    // Populate inputs
    document.getElementById('decisionTitleInput').value = decisionState.title;
    document.getElementById('decisionTitleHeading').textContent = decisionState.title;
    document.getElementById('decisionDescInput').value = decisionState.description;
    document.getElementById('workspaceModeTag').textContent = 'Editing Decision';

    cacheSavedWeights();
    renderAll();
    hideWorkspaceAlert();
    updateSaveStatus('Loaded from server');

    // Automatically calculate and display initial results
    calculateResults(false);
  } catch (err) {
    showWorkspaceAlert('Failed to load decision data.', 'danger');
  }
}

// Initialize default blank decision
function initializeBlankDecision() {
  decisionState = {
    id: null,
    title: 'Untitled Decision',
    description: '',
    options: [
      { id: 'opt_1', name: 'Option Alpha', description: '', attributes: {} },
      { id: 'opt_2', name: 'Option Beta', description: '', attributes: {} }
    ],
    criteria: [
      { id: 'crit_1', name: 'Value & Benefit', weight: 50.0 },
      { id: 'crit_2', name: 'Effort & Cost', weight: 50.0 }
    ],
    ratings: {
      'opt_1___crit_1': 8.0,
      'opt_1___crit_2': 6.0,
      'opt_2___crit_1': 7.0,
      'opt_2___crit_2': 8.0
    },
    constraints: [],
    savedCriteriaWeights: {}
  };

  document.getElementById('decisionTitleInput').value = decisionState.title;
  document.getElementById('decisionTitleHeading').textContent = decisionState.title;
  cacheSavedWeights();
  renderAll();
  updateSaveStatus('New (Unsaved)');
}

function cacheSavedWeights() {
  decisionState.savedCriteriaWeights = {};
  decisionState.criteria.forEach(c => {
    decisionState.savedCriteriaWeights[c.id] = c.weight;
  });
}

function markUnsaved() {
  updateSaveStatus('Unsaved changes');
}

function updateSaveStatus(text) {
  const badge = document.getElementById('saveStatusBadge');
  if (badge) {
    badge.textContent = text;
    if (text.includes('Unsaved')) {
      badge.className = 'badge badge-warning';
    } else {
      badge.className = 'badge badge-blue';
    }
  }
}

// ----------------- RENDERERS -----------------

function renderAll() {
  renderOptionsList();
  renderCriteriaList();
  renderConstraintsList();
  renderMatrix();
  updateWeightSumBadge();
}

function renderOptionsList() {
  const container = document.getElementById('optionsList');
  if (!container) return;

  if (decisionState.options.length === 0) {
    container.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem;">No alternatives added yet.</p>';
    return;
  }

  container.innerHTML = decisionState.options.map((opt, idx) => `
    <div class="dynamic-row" id="optRow_${opt.id}">
      <span style="font-weight: 600; font-size: 0.85rem; width: 24px; color: var(--text-muted);">${idx + 1}.</span>
      <div style="flex: 2;">
        <input type="text" class="form-input" value="${escapeHtml(opt.name)}" placeholder="Alternative name" onchange="updateOptionName('${opt.id}', this.value)" aria-label="Alternative name">
      </div>
      <div style="flex: 2;">
        <input type="text" class="form-input" value="${escapeHtml(opt.description || '')}" placeholder="Notes (optional)" onchange="updateOptionDesc('${opt.id}', this.value)" aria-label="Alternative notes">
      </div>
      <div style="flex: 2;">
        <input type="text" class="form-input" value="${formatAttributes(opt.attributes)}" placeholder="Attributes: e.g. price:1200, hrs:10" onchange="updateOptionAttributes('${opt.id}', this.value)" title="Attributes for hard requirements" aria-label="Attributes">
      </div>
      <button type="button" class="btn btn-sm btn-danger" onclick="removeOption('${opt.id}')" ${decisionState.options.length <= 2 ? 'disabled title="Minimum 2 alternatives required"' : ''} aria-label="Remove alternative">&times;</button>
    </div>
  `).join('');
}

function renderCriteriaList() {
  const container = document.getElementById('criteriaList');
  if (!container) return;

  if (decisionState.criteria.length === 0) {
    container.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem;">No criteria added yet.</p>';
    return;
  }

  container.innerHTML = decisionState.criteria.map((crit, idx) => `
    <div class="dynamic-row" id="critRow_${crit.id}">
      <span style="font-weight: 600; font-size: 0.85rem; width: 24px; color: var(--text-muted);">${idx + 1}.</span>
      <div style="flex: 3;">
        <input type="text" class="form-input" value="${escapeHtml(crit.name)}" placeholder="Criterion name" onchange="updateCriterionName('${crit.id}', this.value)" aria-label="Criterion name">
      </div>
      <div style="flex: 1; max-width: 140px; display: flex; align-items: center; gap: 0.35rem;">
        <input type="number" min="0" max="100" step="1" class="form-input" value="${crit.weight}" onchange="updateCriterionWeight('${crit.id}', this.value)" aria-label="Criterion weight percentage">
        <span style="font-size: 0.85rem; color: var(--text-secondary);">%</span>
      </div>
      <button type="button" class="btn btn-sm btn-danger" onclick="removeCriterion('${crit.id}')" ${decisionState.criteria.length <= 1 ? 'disabled title="Minimum 1 criterion required"' : ''} aria-label="Remove criterion">&times;</button>
    </div>
  `).join('');
}

function renderConstraintsList() {
  const container = document.getElementById('constraintsList');
  if (!container) return;

  if (decisionState.constraints.length === 0) {
    container.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem;">No hard requirements set. (All alternatives are currently eligible).</p>';
    return;
  }

  container.innerHTML = decisionState.constraints.map(con => `
    <div class="dynamic-row" id="conRow_${con.id}">
      <div style="flex: 2;">
        <input type="text" class="form-input" value="${escapeHtml(con.name)}" placeholder="Requirement Label (e.g. Max Price)" onchange="updateConstraintField('${con.id}', 'name', this.value)" aria-label="Requirement label">
      </div>
      <div style="flex: 2;">
        <input type="text" class="form-input" value="${escapeHtml(con.attribute_key)}" placeholder="Attribute (e.g. price)" onchange="updateConstraintField('${con.id}', 'attribute_key', this.value)" aria-label="Attribute key">
      </div>
      <div style="flex: 1; max-width: 100px;">
        <select class="form-select" onchange="updateConstraintField('${con.id}', 'operator', this.value)" aria-label="Comparison operator">
          <option value="<=" ${con.operator === '<=' ? 'selected' : ''}>&le; (Max)</option>
          <option value=">=" ${con.operator === '>=' ? 'selected' : ''}>&ge; (Min)</option>
          <option value="<" ${con.operator === '<' ? 'selected' : ''}>&lt;</option>
          <option value=">" ${con.operator === '>' ? 'selected' : ''}>&gt;</option>
          <option value="==" ${con.operator === '==' ? 'selected' : ''}>== (Exact)</option>
        </select>
      </div>
      <div style="flex: 1.5; max-width: 140px;">
        <input type="number" step="any" class="form-input" value="${con.threshold}" placeholder="Threshold" onchange="updateConstraintField('${con.id}', 'threshold', parseFloat(this.value))" aria-label="Threshold value">
      </div>
      <button type="button" class="btn btn-sm btn-danger" onclick="removeConstraint('${con.id}')" aria-label="Remove requirement">&times;</button>
    </div>
  `).join('');
}

function renderMatrix() {
  const table = document.getElementById('matrixTable');
  if (!table) return;

  if (decisionState.options.length === 0 || decisionState.criteria.length === 0) {
    table.innerHTML = '<tbody><tr><td>Please add at least 2 alternatives and 1 criterion to build the matrix.</td></tr></tbody>';
    return;
  }

  let html = '<thead><tr><th>Alternative</th>';
  decisionState.criteria.forEach(c => {
    html += `<th>${escapeHtml(c.name)} <span style="font-weight: normal; color: var(--text-muted);">(${c.weight}%)</span></th>`;
  });
  html += '</tr></thead><tbody>';

  decisionState.options.forEach(opt => {
    html += `<tr><td><strong>${escapeHtml(opt.name)}</strong></td>`;
    decisionState.criteria.forEach(crit => {
      const key = `${opt.id}___${crit.id}`;
      const currentVal = decisionState.ratings[key] !== undefined ? decisionState.ratings[key] : 7.0;
      decisionState.ratings[key] = currentVal;

      html += `
        <td>
          <input type="number" min="1" max="10" step="0.5" class="form-input matrix-input" 
            value="${currentVal}" 
            onchange="updateRating('${opt.id}', '${crit.id}', this.value)" 
            aria-label="Rating for ${escapeHtml(opt.name)} on ${escapeHtml(crit.name)}">
        </td>
      `;
    });
    html += '</tr>';
  });

  html += '</tbody>';
  table.innerHTML = html;
}

// ----------------- SUB-ENTITY MUTATIONS -----------------

function addOption() {
  const newId = `opt_${Date.now()}`;
  decisionState.options.push({
    id: newId,
    name: `Alternative ${decisionState.options.length + 1}`,
    description: '',
    attributes: {}
  });
  renderOptionsList();
  renderMatrix();
  markUnsaved();
}

function removeOption(id) {
  if (decisionState.options.length <= 2) {
    showToast('A decision requires at least 2 alternatives.', 'warning');
    return;
  }
  decisionState.options = decisionState.options.filter(o => o.id !== id);
  renderOptionsList();
  renderMatrix();
  markUnsaved();
}

function updateOptionName(id, val) {
  const opt = decisionState.options.find(o => o.id === id);
  if (opt) {
    opt.name = val.trim();
    renderMatrix();
    markUnsaved();
  }
}

function updateOptionDesc(id, val) {
  const opt = decisionState.options.find(o => o.id === id);
  if (opt) {
    opt.description = val.trim();
    markUnsaved();
  }
}

function updateOptionAttributes(id, val) {
  const opt = decisionState.options.find(o => o.id === id);
  if (!opt) return;

  // Parse comma-separated key:value pairs, e.g. price:1200, battery:14
  const attrs = {};
  if (val && val.trim()) {
    val.split(',').forEach(part => {
      const pair = part.split(':');
      if (pair.length === 2) {
        const k = pair[0].trim().toLowerCase();
        const num = parseFloat(pair[1].trim());
        if (!isNaN(num)) {
          attrs[k] = num;
        }
      }
    });
  }
  opt.attributes = attrs;
  markUnsaved();
}

function formatAttributes(attrs) {
  if (!attrs || typeof attrs !== 'object') return '';
  return Object.entries(attrs).map(([k, v]) => `${k}:${v}`).join(', ');
}

function addCriterion() {
  const newId = `crit_${Date.now()}`;
  decisionState.criteria.push({
    id: newId,
    name: `Criterion ${decisionState.criteria.length + 1}`,
    weight: 0.0
  });
  renderCriteriaList();
  renderMatrix();
  updateWeightSumBadge();
  markUnsaved();
}

function removeCriterion(id) {
  if (decisionState.criteria.length <= 1) {
    showToast('A decision requires at least 1 criterion.', 'warning');
    return;
  }
  decisionState.criteria = decisionState.criteria.filter(c => c.id !== id);
  renderCriteriaList();
  renderMatrix();
  updateWeightSumBadge();
  markUnsaved();
}

function updateCriterionName(id, val) {
  const crit = decisionState.criteria.find(c => c.id === id);
  if (crit) {
    crit.name = val.trim();
    renderMatrix();
    markUnsaved();
  }
}

function updateCriterionWeight(id, val) {
  const crit = decisionState.criteria.find(c => c.id === id);
  if (crit) {
    const num = parseFloat(val);
    crit.weight = isNaN(num) ? 0.0 : num;
    updateWeightSumBadge();
    renderMatrix();
    markUnsaved();
  }
}

function autoBalanceWeights() {
  if (decisionState.criteria.length === 0) return;
  const count = decisionState.criteria.length;
  const equalShare = parseFloat((100.0 / count).toFixed(2));
  let remaining = 100.0;

  decisionState.criteria.forEach((c, idx) => {
    if (idx === count - 1) {
      c.weight = parseFloat(remaining.toFixed(2));
    } else {
      c.weight = equalShare;
      remaining -= equalShare;
    }
  });

  renderCriteriaList();
  renderMatrix();
  updateWeightSumBadge();
  markUnsaved();
  showToast('Weights auto-balanced equally to 100%.', 'info');
}

function updateWeightSumBadge() {
  const badge = document.getElementById('weightSumBadge');
  if (!badge) return;

  const total = decisionState.criteria.reduce((sum, c) => sum + (c.weight || 0), 0);
  const rounded = Math.round(total * 100) / 100;

  if (Math.abs(rounded - 100.0) < 0.01) {
    badge.className = 'badge badge-success';
    badge.textContent = 'Weights Total: 100% ✓';
  } else {
    badge.className = 'badge badge-warning';
    badge.textContent = `Weights Total: ${rounded}% (Must be 100%)`;
  }
}

function updateRating(optId, critId, val) {
  const num = parseFloat(val);
  const key = `${optId}___${critId}`;
  if (!isNaN(num) && num >= 1.0 && num <= 10.0) {
    decisionState.ratings[key] = num;
  } else {
    decisionState.ratings[key] = 5.0;
  }
  markUnsaved();
}

function addConstraint() {
  const newId = `con_${Date.now()}`;
  decisionState.constraints.push({
    id: newId,
    name: 'Requirement',
    attribute_key: 'price',
    operator: '<=',
    threshold: 1500
  });
  renderConstraintsList();
  markUnsaved();
}

function removeConstraint(id) {
  decisionState.constraints = decisionState.constraints.filter(c => c.id !== id);
  renderConstraintsList();
  markUnsaved();
}

function updateConstraintField(id, field, val) {
  const con = decisionState.constraints.find(c => c.id === id);
  if (con) {
    con[field] = val;
    markUnsaved();
  }
}

// ----------------- SAVE DECISION -----------------

async function saveDecision(showFeedback = true) {
  // Validate inputs
  const title = decisionState.title.trim();
  if (!title) {
    showWorkspaceAlert('Please provide a decision title.', 'danger');
    document.getElementById('titleError').classList.add('visible');
    return false;
  }
  document.getElementById('titleError').classList.remove('visible');

  if (decisionState.options.length < 2) {
    showWorkspaceAlert('At least two alternatives are required to compare choices.', 'danger');
    return false;
  }

  if (decisionState.criteria.length < 1) {
    showWorkspaceAlert('At least one criterion is required.', 'danger');
    return false;
  }

  const weightSum = decisionState.criteria.reduce((s, c) => s + (c.weight || 0), 0);
  if (Math.abs(weightSum - 100.0) > 0.01) {
    showWorkspaceAlert(`Criterion weights must sum to exactly 100%. Current sum: ${weightSum.toFixed(2)}%. Click 'Auto-Balance' to distribute automatically.`, 'warning');
    return false;
  }

  // Format ratings payload
  const ratingsPayload = [];
  decisionState.options.forEach(opt => {
    decisionState.criteria.forEach(crit => {
      const key = `${opt.id}___${crit.id}`;
      const rVal = decisionState.ratings[key] !== undefined ? decisionState.ratings[key] : 7.0;
      ratingsPayload.push({
        option_id: opt.id,
        criterion_id: crit.id,
        rating: rVal
      });
    });
  });

  const payload = {
    title: title,
    description: decisionState.description,
    options: decisionState.options,
    criteria: decisionState.criteria,
    ratings: ratingsPayload,
    constraints: decisionState.constraints
  };

  const saveBtn = document.getElementById('saveDecisionBtn');
  saveBtn.disabled = true;
  saveBtn.innerHTML = '<span class="spinner"></span> Saving...';

  try {
    let res;
    if (decisionState.id) {
      // Update
      res = await apiRequest(`/decisions/${decisionState.id}`, {
        method: 'PUT',
        body: JSON.stringify(payload)
      });
    } else {
      // Create
      res = await apiRequest('/decisions', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
    }

    if (res.ok) {
      const savedData = await res.json();
      decisionState.id = savedData.id;
      // Sync IDs if generated by DB
      decisionState.options = savedData.options;
      decisionState.criteria = savedData.criteria;
      cacheSavedWeights();

      // Update URL query parameter without full reload
      const newUrl = `${window.location.pathname}?id=${savedData.id}`;
      window.history.replaceState({ path: newUrl }, '', newUrl);

      updateSaveStatus(`Saved at ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`);
      if (showFeedback) {
        showToast('Decision saved successfully!', 'success');
      }
      hideWorkspaceAlert();
      return true;
    } else {
      const err = await res.json();
      showWorkspaceAlert(err.detail || 'Failed to save decision.', 'danger');
      return false;
    }
  } catch (err) {
    showWorkspaceAlert('Error connecting to server to save.', 'danger');
    return false;
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
        <polyline points="17 21 17 13 7 13 7 21"></polyline>
        <polyline points="7 3 7 8 15 8"></polyline>
      </svg>
      <span>Save Decision</span>
    `;
  }
}

// ----------------- CALCULATION & RESULTS -----------------

async function calculateResults(notify = true) {
  // Ensure decision is saved first so we have DB IDs
  if (!decisionState.id) {
    const saved = await saveDecision(false);
    if (!saved) return;
  }

  const calcBtn = document.getElementById('calculateBtn');
  calcBtn.disabled = true;
  calcBtn.innerHTML = '<span class="spinner"></span> Calculating...';

  try {
    const res = await apiRequest(`/decisions/${decisionState.id}/calculate`, {
      method: 'POST'
    });

    if (res.ok) {
      const evalData = await res.json();
      renderResults(evalData);
      renderChart(evalData);
      renderSimulator();
      document.getElementById('resultsSection').style.display = 'block';

      if (notify) {
        showToast('Scores calculated and rankings updated!', 'success');
        document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
      }
    } else {
      const err = await res.json();
      showWorkspaceAlert(err.detail || 'Calculation error.', 'danger');
    }
  } catch (err) {
    showWorkspaceAlert('Failed to calculate results.', 'danger');
  } finally {
    calcBtn.disabled = false;
    calcBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
        <polyline points="17 6 23 6 23 12"></polyline>
      </svg>
      <span>Calculate Results</span>
    `;
  }
}

function renderResults(evalData) {
  const tbody = document.getElementById('resultsTableBody');
  const summaryEl = document.getElementById('resultsSummaryText');

  summaryEl.textContent = evalData.summary_message;

  tbody.innerHTML = evalData.options.map(opt => {
    let rankClass = 'rank-other';
    if (opt.is_eligible) {
      if (opt.rank === 1) rankClass = 'rank-1';
      else if (opt.rank === 2) rankClass = 'rank-2';
    }

    const rankDisplay = opt.is_eligible 
      ? `<span class="rank-circle ${rankClass}">${opt.rank}</span>` 
      : `<span class="rank-circle rank-other" title="Excluded by hard requirements">&mdash;</span>`;

    const tieBadge = opt.is_tied ? '<span class="badge badge-purple" style="margin-left: 0.35rem;">Tied</span>' : '';

    const eligibilityBadge = opt.is_eligible
      ? '<span class="badge badge-success">Eligible</span>'
      : '<span class="badge badge-danger">Ineligible</span>';

    // Breakdown pills
    const breakdownPills = Object.entries(opt.criteria_contributions || {}).map(([critId, pts]) => {
      const crit = decisionState.criteria.find(c => c.id === critId);
      const name = crit ? crit.name : 'Criterion';
      const r = opt.criteria_ratings ? opt.criteria_ratings[critId] : '';
      return `<span style="display: inline-block; background-color: var(--bg-card); padding: 0.15rem 0.5rem; border-radius: var(--radius-sm); font-size: 0.775rem; margin: 0.15rem; border: 1px solid var(--border-color);">
        ${escapeHtml(name)}: <strong>${pts.toFixed(2)} pts</strong> (r:${r})
      </span>`;
    }).join('');

    let constraintNote = '';
    if (!opt.is_eligible && opt.failed_constraints.length > 0) {
      constraintNote = `
        <div style="color: var(--color-error); font-size: 0.8rem; margin-top: 0.35rem;">
          ${opt.failed_constraints.map(r => `&bull; ${escapeHtml(r)}`).join('<br>')}
        </div>
      `;
    }

    return `
      <tr style="${!opt.is_eligible ? 'opacity: 0.75;' : ''}">
        <td>${rankDisplay} ${tieBadge}</td>
        <td>
          <strong>${escapeHtml(opt.option_name)}</strong>
          ${constraintNote}
        </td>
        <td>${eligibilityBadge}</td>
        <td>
          <span style="font-size: 1.25rem; font-weight: 700; color: ${opt.is_eligible ? 'var(--accent-primary)' : 'var(--text-muted)'};">
            ${opt.display_score.toFixed(2)}
          </span>
          <span style="font-size: 0.8rem; color: var(--text-muted);">/ 10</span>
        </td>
        <td>${breakdownPills}</td>
      </tr>
    `;
  }).join('');
}

// Render lightweight accessible SVG Score Chart
function renderChart(evalData) {
  const container = document.getElementById('chartVisualization');
  if (!container) return;

  const maxScore = 10.0;
  const barHeight = 28;
  const gap = 14;
  const width = 600;
  const height = evalData.options.length * (barHeight + gap) + 20;

  let svgHtml = `
    <svg viewBox="0 0 ${width} ${height}" style="width: 100%; max-width: 600px; height: auto;" aria-label="Score Comparison Chart">
  `;

  evalData.options.forEach((opt, idx) => {
    const y = idx * (barHeight + gap) + 10;
    const barWidth = Math.max(8, (opt.score / maxScore) * (width - 180));
    const fillColor = !opt.is_eligible ? '#64748B' : (opt.rank === 1 ? '#22C55E' : '#3B82F6');

    svgHtml += `
      <!-- Label -->
      <text x="10" y="${y + 18}" fill="var(--text-primary)" font-size="12" font-family="var(--font-sans)">
        ${escapeHtml(opt.option_name.substring(0, 18))}
      </text>

      <!-- Bar Background -->
      <rect x="140" y="${y}" width="${width - 180}" height="${barHeight}" rx="4" fill="rgba(255,255,255,0.05)" />

      <!-- Bar Fill -->
      <rect x="140" y="${y}" width="${barWidth}" height="${barHeight}" rx="4" fill="${fillColor}" />

      <!-- Score Label -->
      <text x="${140 + barWidth + 8}" y="${y + 18}" fill="var(--text-primary)" font-size="12" font-weight="600" font-family="var(--font-sans)">
        ${opt.display_score.toFixed(2)} ${!opt.is_eligible ? '(Ineligible)' : ''}
      </text>
    `;
  });

  svgHtml += '</svg>';
  container.innerHTML = svgHtml;
}

// ----------------- WHAT-IF SIMULATOR -----------------

function renderSimulator() {
  const container = document.getElementById('simulatorSliders');
  if (!container) return;

  temporaryWeights = {};
  decisionState.criteria.forEach(c => {
    temporaryWeights[c.id] = c.weight;
  });

  container.innerHTML = decisionState.criteria.map(crit => `
    <div class="slider-row" id="simSliderRow_${crit.id}">
      <span style="font-size: 0.9rem; font-weight: 500; word-break: break-word;">${escapeHtml(crit.name)}</span>
      <input type="range" min="0" max="100" step="1" class="range-slider" value="${crit.weight}"
        oninput="handleSimulatorSliderChange('${crit.id}', this.value)" aria-label="Simulator weight for ${escapeHtml(crit.name)}">
      <span id="simVal_${crit.id}" style="font-size: 0.9rem; font-weight: 700; text-align: right; color: var(--accent-primary);">
        ${crit.weight}%
      </span>
    </div>
  `).join('');
}

async function handleSimulatorSliderChange(critId, val) {
  const num = parseFloat(val);
  temporaryWeights[critId] = num;

  const displayEl = document.getElementById(`simVal_${critId}`);
  if (displayEl) {
    displayEl.textContent = `${num}%`;
  }

  // Recalculate weights in memory and evaluate
  const total = Object.values(temporaryWeights).reduce((a, b) => a + b, 0);

  // If weights don't equal 100%, we normalize or check with backend
  // When total equals 100%, call calculation endpoint with temporary weights
  if (Math.abs(total - 100.0) < 0.01 && decisionState.id) {
    try {
      const res = await apiRequest(`/decisions/${decisionState.id}/calculate`, {
        method: 'POST',
        body: JSON.stringify({ temporary_weights: temporaryWeights })
      });
      if (res.ok) {
        const evalData = await res.json();
        renderResults(evalData);
        renderChart(evalData);
      }
    } catch (e) {
      // ignore transient slider fetch error
    }
  }
}

function resetSimulation() {
  decisionState.criteria.forEach(c => {
    temporaryWeights[c.id] = decisionState.savedCriteriaWeights[c.id] || c.weight;
    const slider = document.querySelector(`#simSliderRow_${c.id} input[type="range"]`);
    if (slider) slider.value = temporaryWeights[c.id];
    const displayEl = document.getElementById(`simVal_${c.id}`);
    if (displayEl) displayEl.textContent = `${temporaryWeights[c.id]}%`;
  });

  // Recalculate with original weights
  calculateResults(false);
  showToast('Simulator reset to saved baseline weights.', 'info');
}

async function applySimulationWeights() {
  const total = Object.values(temporaryWeights).reduce((a, b) => a + b, 0);
  if (Math.abs(total - 100.0) > 0.01) {
    showToast(`Temporary weights sum to ${total}%. Must sum to 100% to save.`, 'warning');
    return;
  }

  decisionState.criteria.forEach(c => {
    if (temporaryWeights[c.id] !== undefined) {
      c.weight = temporaryWeights[c.id];
    }
  });

  renderCriteriaList();
  renderMatrix();
  updateWeightSumBadge();

  const saved = await saveDecision(true);
  if (saved) {
    calculateResults(false);
    showToast('Simulation weights saved as new permanent criteria weights!', 'success');
  }
}

// ----------------- CSV EXPORT -----------------

async function exportCsv() {
  if (!decisionState.id) {
    const saved = await saveDecision(false);
    if (!saved) return;
  }

  showToast('Preparing CSV export...', 'info');

  try {
    const res = await apiRequest(`/decisions/${decisionState.id}/export`);
    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const cleanTitle = decisionState.title.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 30);
      a.download = `decision_${cleanTitle}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      showToast('CSV export downloaded!', 'success');
    } else {
      showToast('Failed to export CSV.', 'error');
    }
  } catch (err) {
    showToast('Error exporting CSV.', 'error');
  }
}

// ----------------- ALERTS & HELPERS -----------------

function showWorkspaceAlert(msg, type = 'info') {
  const alertEl = document.getElementById('workspaceAlert');
  if (alertEl) {
    alertEl.className = `alert alert-${type}`;
    alertEl.textContent = msg;
    alertEl.style.display = 'block';
  }
}

function hideWorkspaceAlert() {
  const alertEl = document.getElementById('workspaceAlert');
  if (alertEl) {
    alertEl.style.display = 'none';
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
