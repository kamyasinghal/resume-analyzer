const $ = id => document.getElementById(id);

const uploadZone   = $('uploadZone');
const resumeUpload = $('resumeUpload');
const browseBtn    = $('browseBtn');
const uploadIdle   = $('uploadIdle');
const uploadSelected = $('uploadSelected');
const fileName     = $('fileName');
const fileSize     = $('fileSize');
const fileRemove   = $('fileRemove');
const jobDesc      = $('jobDescription');
const charCount    = $('charCount');
const analyzeBtn   = $('analyzeBtn');
const analyzeNote  = $('analyzeNote');
const emptyState   = $('emptyState');
const resultsInner = $('resultsInner');

let skillsChart = null;

// ── THEME TOGGLE ──────────────────────────────────
$('themeToggle').addEventListener('click', () => {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  html.setAttribute('data-theme', isDark ? 'light' : 'dark');
  $('toggleLabel').textContent = isDark ? 'Light' : 'Dark';
});

// ── FILE UPLOAD ───────────────────────────────────
browseBtn.addEventListener('click', () => resumeUpload.click());
uploadZone.addEventListener('click', e => {
  if (e.target !== browseBtn && uploadSelected.style.display === 'none') resumeUpload.click();
});
uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
uploadZone.addEventListener('drop', e => {
  e.preventDefault(); uploadZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
});
resumeUpload.addEventListener('change', () => { if (resumeUpload.files[0]) setFile(resumeUpload.files[0]); });
fileRemove.addEventListener('click', e => { e.stopPropagation(); clearFile(); });

function setFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf','docx'].includes(ext)) { showNote('Only PDF and DOCX supported.', true); return; }
  const dt = new DataTransfer(); dt.items.add(file); resumeUpload.files = dt.files;
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
function formatBytes(b) {
  if (b < 1024) return b + ' B';
  if (b < 1048576) return (b/1024).toFixed(1) + ' KB';
  return (b/1048576).toFixed(1) + ' MB';
}

// ── TEXTAREA ──────────────────────────────────────
jobDesc.addEventListener('input', () => {
  charCount.textContent = jobDesc.value.length ? jobDesc.value.length.toLocaleString() + ' chars' : '0 chars';
  updateBtn();
});

// ── BUTTON STATE ──────────────────────────────────
function updateBtn() {
  const hasFile = resumeUpload.files && resumeUpload.files.length > 0;
  analyzeBtn.disabled = !hasFile;
  analyzeNote.textContent = hasFile
    ? (jobDesc.value.trim() ? 'Ready to analyze' : "No JD? We'll still score your resume")
    : 'Upload a resume to begin';
  analyzeNote.style.color = '';
}
function showNote(msg, err) {
  analyzeNote.textContent = msg;
  analyzeNote.style.color = err ? '#dc2626' : '';
  setTimeout(() => { analyzeNote.style.color = ''; updateBtn(); }, 3000);
}

// ── TABS ──────────────────────────────────────────
document.addEventListener('click', e => {
  if (!e.target.classList.contains('tab-btn')) return;
  document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.style.display = 'none');
  e.target.classList.add('active');
  $('tab-' + e.target.dataset.tab).style.display = 'block';
});

// ── ANALYZE ───────────────────────────────────────
analyzeBtn.addEventListener('click', async () => {
  const file = resumeUpload.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append('resume', file);
  if (jobDesc.value.trim()) fd.append('job_description', jobDesc.value.trim());

  analyzeBtn.disabled = true;
  analyzeBtn.classList.add('loading');
  analyzeBtn.querySelector('.cta-text').textContent = 'Analyzing…';
  analyzeNote.textContent = 'Extracting and scoring…';

  try {
    const res = await fetch('/analyze', { method: 'POST', body: fd });
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || `Error ${res.status}`); }
    renderResults(await res.json());
  } catch(err) {
    showNote('Error: ' + err.message, true);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.classList.remove('loading');
    analyzeBtn.querySelector('.cta-text').textContent = 'Analyze resume';
    updateBtn();
  }
});

// ── RENDER ────────────────────────────────────────
function renderResults(data) {
  emptyState.style.display = 'none';
  resultsInner.style.display = 'flex';

  document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.style.display = 'none');
  document.querySelector('[data-tab="skills"]').classList.add('active');
  $('tab-skills').style.display = 'block';

  const score   = Number(data.ats_score) || 0;
  const matched = data.skills || [];
  const missing = data.missing_skills || [];

  // Score ring
  const circumference = 176;
  const offset = circumference - (score / 100) * circumference;
  setTimeout(() => { $('scoreRingFill').style.strokeDashoffset = offset; }, 100);

  // Score bar
  setTimeout(() => { $('scoreBarFill').style.width = score + '%'; }, 200);

  // Verdict
  const verdicts = [[75,'Excellent match'],[55,'Good match'],[35,'Fair match'],[0,'Needs work']];
  $('scoreVerdict').textContent = verdicts.find(([t]) => score >= t)[1];

  // Animated counters
  animateCount($('scoreNum'), 0, score, 1200);
  animateCount($('statMatched'), 0, matched.length, 900);
  animateCount($('statMissing'), 0, missing.length, 900);
  const edu = Array.isArray(data.education) ? data.education[0] : (data.education || '—');
  $('statEdu').textContent = edu.length > 9 ? edu.slice(0,9) + '…' : edu;

  // Tags
  renderTags($('matchedTags'), matched, 'tag-m');
  renderTags($('missingTags'), missing, 'tag-x');

  // Skills chart
  renderSkillsChart(matched);

  // Experience & education
  const exps = Array.isArray(data.experience) ? data.experience : [data.experience || 'Not detected'];
  const expList = $('expList');
  expList.innerHTML = '';
  exps.forEach((e, i) => {
    const d = document.createElement('div');
    d.className = 'exp-item';
    d.style.animationDelay = i * 80 + 'ms';
    d.innerHTML = `<div class="exp-dot"></div><div class="exp-text">${e}</div>`;
    expList.appendChild(d);
  });
  const edus = Array.isArray(data.education) ? data.education : [data.education || 'Not detected'];
  $('eduBlock').innerHTML = `<div class="edu-label">Education</div><div class="edu-text">${edus.join('<br>')}</div>`;

  // AI
  const sections = parseAI(data.ai_feedback);
  renderList($('strengthsList'), sections.strengths);
  renderList($('weaknessesList'), sections.weaknesses);
  const sugg = $('suggestions');
  sugg.innerHTML = '';
  [...missing.map(s => `Add missing skill: ${s}`), ...sections.suggestions]
    .forEach(s => { const li = document.createElement('li'); li.textContent = s; sugg.appendChild(li); });

  resultsInner.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── HELPERS ───────────────────────────────────────
function renderTags(container, items, cls) {
  container.innerHTML = '';
  if (!items.length) {
    const t = document.createElement('span');
    t.className = 'tag tag-empty'; t.textContent = 'None detected';
    container.appendChild(t); return;
  }
  items.forEach((item, i) => {
    const t = document.createElement('span');
    t.className = `tag ${cls}`; t.textContent = item;
    t.style.animationDelay = i * 40 + 'ms';
    container.appendChild(t);
  });
}

function renderSkillsChart(skills) {
  if (skillsChart) { skillsChart.destroy(); skillsChart = null; }
  if (!skills.length) return;
  const palette = ['#6366f1','#06b6d4','#10b981','#f59e0b','#ef4444','#8b5cf6','#f97316','#14b8a6'];
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  skillsChart = new Chart($('skillsChart').getContext('2d'), {
    type: 'doughnut',
    data: {
      labels: skills,
      datasets: [{ data: Array(skills.length).fill(1), backgroundColor: skills.map((_,i) => palette[i % palette.length]), borderWidth: 0, spacing: 2 }]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: {
        legend: { display: true, position: 'bottom', labels: { color: isDark ? '#94a3b8' : '#64748b', font: { family: 'Inter', size: 11 }, padding: 12, boxWidth: 10, boxHeight: 10 } },
        tooltip: { backgroundColor: isDark ? '#1c1c28' : '#fff', borderColor: isDark ? '#2a2a3a' : '#e2e8f0', borderWidth: 1, titleColor: isDark ? '#f1f5f9' : '#18181b', bodyColor: isDark ? '#94a3b8' : '#64748b' }
      }
    }
  });
}

function renderList(el, items) {
  el.innerHTML = '';
  (items.length ? items : ['Not available']).forEach(s => {
    const li = document.createElement('li'); li.textContent = s; el.appendChild(li);
  });
}

function parseAI(text) {
  const out = { strengths: [], weaknesses: [], suggestions: [] };
  if (!text) return out;
  let section = null;
  for (const raw of text.split('\n')) {
    const line = raw.trim();
    if (!line) continue;
    if (/^strengths:/i.test(line))   { section = 'strengths';   continue; }
    if (/^weaknesses:/i.test(line))  { section = 'weaknesses';  continue; }
    if (/^suggestions:/i.test(line)) { section = 'suggestions'; continue; }
    if (section) { const c = line.replace(/^[-\d\.\)\s]+/, '').trim(); if (c) out[section].push(c); }
  }
  return out;
}

function animateCount(el, from, to, duration) {
  const start = performance.now();
  const tick = now => {
    const p = Math.min((now - start) / duration, 1);
    el.textContent = Math.round(from + (to - from) * (1 - Math.pow(1 - p, 3)));
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

updateBtn();
