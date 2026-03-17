// =============================================
// ResumeIQ — Interactive Frontend Script
// =============================================

const $ = id => document.getElementById(id);

// DOM refs
const uploadZone    = $('uploadZone');
const resumeUpload  = $('resumeUpload');
const browseBtn     = $('browseBtn');
const uploadIdle    = $('uploadIdle');
const uploadSelected= $('uploadSelected');
const fileName      = $('fileName');
const fileSize      = $('fileSize');
const fileRemove    = $('fileRemove');
const jobDesc       = $('jobDescription');
const charCount     = $('charCount');
const analyzeBtn    = $('analyzeBtn');
const analyzeNote   = $('analyzeNote');
const emptyState    = $('emptyState');
const resultsInner  = $('resultsInner');

let atsChart = null;
let skillsChart = null;

// =============================================
// FILE UPLOAD LOGIC
// =============================================

browseBtn.addEventListener('click', () => resumeUpload.click());
uploadZone.addEventListener('click', e => {
  if (e.target !== browseBtn && !uploadSelected.style.display.includes('flex')) {
    resumeUpload.click();
  }
});

uploadZone.addEventListener('dragover', e => {
  e.preventDefault();
  uploadZone.classList.add('drag-over');
});
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
});

resumeUpload.addEventListener('change', () => {
  if (resumeUpload.files[0]) setFile(resumeUpload.files[0]);
});

fileRemove.addEventListener('click', e => {
  e.stopPropagation();
  clearFile();
});

function setFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf','docx'].includes(ext)) {
    showNote('Only PDF and DOCX files are supported.', true);
    return;
  }
  // Sync to input
  const dt = new DataTransfer();
  dt.items.add(file);
  resumeUpload.files = dt.files;

  fileName.textContent = file.name;
  fileSize.textContent = formatBytes(file.size);
  uploadIdle.style.display = 'none';
  uploadSelected.style.display = 'flex';
  updateBtn();
}

function clearFile() {
  resumeUpload.value = '';
  uploadIdle.style.display = '';
  uploadSelected.style.display = 'none';
  updateBtn();
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + ' KB';
  return (bytes/1024/1024).toFixed(1) + ' MB';
}

// =============================================
// TEXTAREA CHAR COUNT
// =============================================

jobDesc.addEventListener('input', () => {
  const n = jobDesc.value.length;
  charCount.textContent = n > 0 ? `${n.toLocaleString()} chars` : '0 chars';
  updateBtn();
});

// =============================================
// BUTTON STATE
// =============================================

function updateBtn() {
  const hasFile = resumeUpload.files && resumeUpload.files.length > 0;
  analyzeBtn.disabled = !hasFile;
  analyzeNote.textContent = hasFile
    ? (jobDesc.value.trim() ? 'Ready to analyze' : 'No JD? We\'ll still score your resume')
    : 'Upload a resume to begin';
}

function showNote(msg, isError = false) {
  analyzeNote.textContent = msg;
  analyzeNote.style.color = isError ? 'var(--red)' : 'var(--text-3)';
  setTimeout(() => {
    analyzeNote.style.color = '';
    updateBtn();
  }, 3000);
}

// =============================================
// TABS
// =============================================

document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.style.display = 'none');
    tab.classList.add('active');
    $('tab-' + tab.dataset.tab).style.display = 'block';
  });
});

// =============================================
// ANALYZE
// =============================================

analyzeBtn.addEventListener('click', async () => {
  const file = resumeUpload.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('resume', file);
  const jd = jobDesc.value.trim();
  if (jd) formData.append('job_description', jd);

  // Loading state
  analyzeBtn.disabled = true;
  analyzeBtn.classList.add('loading');
  analyzeBtn.querySelector('.btn-text').textContent = 'Analyzing…';
  analyzeNote.textContent = 'Extracting text and scoring…';

  try {
    const res = await fetch('/analyze', { method: 'POST', body: formData });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `Server error ${res.status}`);
    }
    const data = await res.json();
    renderResults(data);
  } catch (err) {
    console.error(err);
    showNote('Error: ' + err.message, true);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.classList.remove('loading');
    analyzeBtn.querySelector('.btn-text').textContent = 'Analyze Resume';
    updateBtn();
  }
});

// =============================================
// RENDER RESULTS
// =============================================

function renderResults(data) {
  emptyState.style.display = 'none';
  resultsInner.style.display = 'flex';

  // Reset tabs to Skills
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.style.display = 'none');
  document.querySelector('[data-tab="skills"]').classList.add('active');
  $('tab-skills').style.display = 'block';

  const score = Number(data.ats_score) || 0;
  const matched = data.skills || [];
  const missing = data.missing_skills || [];

  // Score ring
  renderScoreRing(score);

  // Verdict
  const verdict = score >= 75 ? 'Excellent match' : score >= 55 ? 'Good match' : score >= 35 ? 'Fair match' : 'Needs work';
  $('scoreVerdict').textContent = verdict;

  // Score bar (slight delay for animation)
  setTimeout(() => {
    $('scoreBarFill').style.width = score + '%';
  }, 300);

  // Stats
  animateCount($('scoreNum'), 0, score, 1200);
  animateCount($('statMatched'), 0, matched.length, 800);
  animateCount($('statMissing'), 0, missing.length, 800);
  const edu = Array.isArray(data.education) ? data.education[0] : (data.education || '–');
  $('statEdu').textContent = edu.length > 8 ? edu.slice(0,8) + '…' : edu || '–';

  // Tags
  renderTags($('matchedTags'), matched, 'tag-matched');
  renderTags($('missingTags'), missing, 'tag-missing');

  // Skills chart
  renderSkillsChart(matched);

  // Experience & Education
  renderExperience(data.experience, data.education);

  // AI feedback
  const sections = parseAI(data.ai_feedback);
  renderList($('strengthsList'), sections.strengths);
  renderList($('weaknessesList'), sections.weaknesses);
  renderSuggestions(missing, sections.suggestions);

  // Scroll into view
  resultsInner.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// =============================================
// SCORE RING
// =============================================

function renderScoreRing(score) {
  const ctx = $('atsRing').getContext('2d');
  if (atsChart) atsChart.destroy();

  const color = score >= 75 ? '#c8f55a' : score >= 55 ? '#57a8ff' : score >= 35 ? '#f59e0b' : '#ff5757';

  atsChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [0, 100],
        backgroundColor: [color, '#18181f'],
        borderWidth: 0,
        borderRadius: 4,
      }]
    },
    options: {
      cutout: '80%',
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } }
    }
  });

  let current = 0;
  const target = score;
  const duration = 1200;
  const steps = 60;
  const increment = target / steps;
  const interval = setInterval(() => {
    current = Math.min(current + increment, target);
    atsChart.data.datasets[0].data = [current, 100 - current];
    atsChart.update('none');
    if (current >= target) clearInterval(interval);
  }, duration / steps);
}

// =============================================
// SKILLS CHART
// =============================================

function renderSkillsChart(skills) {
  const ctx = $('skillsChart').getContext('2d');
  if (skillsChart) skillsChart.destroy();

  if (!skills.length) return;

  const palette = ['#c8f55a','#57a8ff','#a78bff','#f59e0b','#ff5757','#06b6d4','#f97316','#34d399'];

  skillsChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: skills,
      datasets: [{
        data: Array(skills.length).fill(1),
        backgroundColor: skills.map((_,i) => palette[i % palette.length]),
        borderWidth: 0,
        borderRadius: 3,
        spacing: 2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: {
            color: '#9896b0',
            font: { family: "'DM Mono'", size: 10 },
            padding: 12,
            boxWidth: 10,
            boxHeight: 10,
          }
        },
        tooltip: {
          backgroundColor: '#18181f',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          titleColor: '#f0eff8',
          bodyColor: '#9896b0',
          callbacks: { label: ctx => ` ${ctx.label}` }
        }
      }
    }
  });
}

// =============================================
// HELPERS
// =============================================

function renderTags(container, items, cls) {
  container.innerHTML = '';
  if (!items.length) {
    const tag = document.createElement('span');
    tag.className = 'tag tag-empty';
    tag.textContent = 'None detected';
    container.appendChild(tag);
    return;
  }
  items.forEach((item, i) => {
    const tag = document.createElement('span');
    tag.className = `tag ${cls}`;
    tag.textContent = item;
    tag.style.animationDelay = `${i * 40}ms`;
    container.appendChild(tag);
  });
}

function renderExperience(experience, education) {
  const expList = $('expList');
  const eduBlock = $('eduBlock');
  expList.innerHTML = '';
  eduBlock.innerHTML = '';

  const exps = Array.isArray(experience) ? experience : (experience ? [experience] : ['Not clearly detected']);
  exps.forEach((e, i) => {
    const div = document.createElement('div');
    div.className = 'exp-item';
    div.style.animationDelay = `${i * 80}ms`;
    div.innerHTML = `<div class="exp-dot"></div><div class="exp-text">${e}</div>`;
    expList.appendChild(div);
  });

  const edus = Array.isArray(education) ? education : (education ? [education] : ['Not detected']);
  eduBlock.innerHTML = `
    <div class="edu-label">Education</div>
    <div class="edu-text">${edus.join('<br>')}</div>
  `;
}

function renderList(el, items) {
  el.innerHTML = '';
  const list = items.length ? items : ['Not available'];
  list.forEach(item => {
    const li = document.createElement('li');
    li.textContent = item;
    el.appendChild(li);
  });
}

function renderSuggestions(missing, aiSuggestions) {
  const el = $('suggestions');
  el.innerHTML = '';
  const items = [];
  if (missing.length) missing.forEach(s => items.push(`Add missing skill to resume: ${s}`));
  if (aiSuggestions.length) aiSuggestions.forEach(s => items.push(s));
  if (!items.length) items.push('Keep resume concise, tailored, and keyword-rich.');

  items.forEach(item => {
    const li = document.createElement('li');
    li.textContent = item;
    el.appendChild(li);
  });
}

function parseAI(text) {
  const out = { strengths: [], weaknesses: [], suggestions: [] };
  if (!text) return out;
  let section = null;
  for (const raw of text.split('\n')) {
    const line = raw.trim();
    if (!line) continue;
    if (/^strengths:/i.test(line)) { section = 'strengths'; continue; }
    if (/^weaknesses:/i.test(line)) { section = 'weaknesses'; continue; }
    if (/^suggestions:/i.test(line)) { section = 'suggestions'; continue; }
    if (section) {
      const clean = line.replace(/^[-\d\.\)\s]+/, '').trim();
      if (clean) out[section].push(clean);
    }
  }
  return out;
}

function animateCount(el, from, to, duration) {
  const start = performance.now();
  const update = now => {
    const p = Math.min((now - start) / duration, 1);
    const ease = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(from + (to - from) * ease);
    if (p < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

// Init
updateBtn();
