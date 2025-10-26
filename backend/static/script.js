// --- DOM Elements ---
const uploadArea = document.getElementById("uploadArea");
const resumeUpload = document.getElementById("resumeUpload");
const uploadBtn = document.getElementById("uploadBtn");
const fileNameSpan = document.getElementById("fileName");
const analyzeBtn = document.getElementById("analyzeBtn");

const dashboardDiv = document.getElementById("dashboard");
const skillsEl = document.getElementById("skills");
const experienceEl = document.getElementById("experience");
const educationEl = document.getElementById("education");
const suggestionsEl = document.getElementById("suggestions");
const aiFeedbackEl = document.getElementById("aiFeedback");
const strengthsListEl = document.getElementById("strengthsList");
const weaknessesListEl = document.getElementById("weaknessesList");

let atsChart = null;
let skillsChart = null;

// --- Upload & Drag/Drop ---
uploadBtn.addEventListener("click", () => resumeUpload.click());

uploadArea.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadArea.style.backgroundColor = "#CFFCF1";
});
uploadArea.addEventListener("dragleave", (e) => {
  e.preventDefault();
  uploadArea.style.backgroundColor = "#E6FFFA";
});
uploadArea.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadArea.style.backgroundColor = "#E6FFFA";
  const files = e.dataTransfer.files;
  if (files.length) {
    resumeUpload.files = files;
    fileNameSpan.textContent = files[0].name;
  }
});

resumeUpload.addEventListener("change", () => {
  if (resumeUpload.files.length) fileNameSpan.textContent = resumeUpload.files[0].name;
});

// --- Helper functions ---
function destroyChart(chart) {
  if (chart) chart.destroy();
}

function addSuggestion(text) {
  const li = document.createElement("li");
  li.textContent = text;
  suggestionsEl.appendChild(li);
}

function clearSuggestionsKeepDefaults() {
  suggestionsEl.innerHTML = `
    <li>Add more keywords related to job description</li>
    <li>Highlight leadership experiences</li>
    <li>Ensure consistent font styles</li>
  `;
}

function fillStrengthsWeaknesses(strengthsArr, weaknessesArr) {
  strengthsListEl.innerHTML = "";
  weaknessesListEl.innerHTML = "";

  if (Array.isArray(strengthsArr) && strengthsArr.length) {
    strengthsArr.forEach(s => {
      const li = document.createElement("li");
      li.textContent = s;
      strengthsListEl.appendChild(li);
    });
  } else {
    const li = document.createElement("li");
    li.textContent = "Not available";
    strengthsListEl.appendChild(li);
  }

  if (Array.isArray(weaknessesArr) && weaknessesArr.length) {
    weaknessesArr.forEach(w => {
      const li = document.createElement("li");
      li.textContent = w;
      weaknessesListEl.appendChild(li);
    });
  } else {
    const li = document.createElement("li");
    li.textContent = "Not available";
    weaknessesListEl.appendChild(li);
  }
}

function parseAIFeedbackToSections(aiText) {
  const sections = { strengths: [], weaknesses: [], suggestions: [], raw: aiText || "" };
  if (!aiText) return sections;

  const lines = aiText.split("\n").map(l => l.trim()).filter(l => l !== "");
  let current = null;

  for (let line of lines) {
    if (line.startsWith("Strengths:")) { current = "strengths"; continue; }
    if (line.startsWith("Weaknesses:")) { current = "weaknesses"; continue; }
    if (line.startsWith("Suggestions:")) { current = "suggestions"; continue; }

    if (current) {
      const match = line.replace(/^[-\d\.\)\s]+/, "").trim();
      if (match) sections[current].push(match);
    }
  }

  return sections;
}



// --- Main Analyze Button ---
analyzeBtn.addEventListener("click", async () => {
  const file = resumeUpload.files[0];
  const jobDesc = document.getElementById("jobDescription").value;
  const formData = new FormData();
  if (file) formData.append("resume", file);
  if (jobDesc) formData.append("job_description", jobDesc);

  analyzeBtn.disabled = true;
  analyzeBtn.innerText = "Analyzing...";

  try {
    const res = await fetch("/analyze", { method: "POST", body: formData });

    if (!res.ok) {
      let errData = {};
      try { errData = await res.json(); } catch {}
      throw new Error(errData.error || `Server returned ${res.status}`);
    }

    const data = await res.json();

    // --- Populate basic info ---
    skillsEl.innerText = data.skills?.length ? data.skills.join(", ") : "Not detected";
    experienceEl.innerText = data.experience || "Not specified";
    educationEl.innerText = data.education || "Not specified";
    dashboardDiv.style.display = "block";

    // --- ATS Score ---
    const ctx1 = document.getElementById("overallScoreChart").getContext("2d");
    let score = 0;
    const targetScore = data.ats_score ? Number(data.ats_score) : 0;
    const scoreText = document.getElementById("scoreText");

    destroyChart(atsChart);
    atsChart = new Chart(ctx1, {
      type: "doughnut",
      data: { labels: ["Score", "Remaining"], datasets: [{ data: [0,100], backgroundColor: ["#0D9488","#F0FDFA"], borderWidth:0 }] },
      options: { cutout: "75%", responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}} }
    });

    await new Promise(resolve => {
      const interval = setInterval(() => {
        if (score >= targetScore) { clearInterval(interval); resolve(); return; }
        score++;
        atsChart.data.datasets[0].data = [score, 100 - score];
        atsChart.update();
        scoreText.innerText = `${score}%`;
      }, 20);
    });

    scoreText.innerText = `${targetScore}%`;
    atsChart.data.datasets[0].data = [targetScore, 100 - targetScore];
    atsChart.update();

    // --- Skills chart ---
    const ctx2 = document.getElementById("skillsChart").getContext("2d");
    destroyChart(skillsChart);
    const skillLabels = data.skills?.length ? data.skills : ["No skills detected"];
    const skillData = data.skills?.length ? Array(data.skills.length).fill(1) : [1];

    skillsChart = new Chart(ctx2, {
      type: "doughnut",
      data: { labels: skillLabels, datasets:[{data: skillData, backgroundColor:["#0D9488","#F97316","#06B6D4","#A78BFA","#F59E0B"], borderWidth:0}] },
      options: { responsive:true, maintainAspectRatio:false, plugins:{legend:{position:"bottom"}} }
    });

    // --- Suggestions ---
    clearSuggestionsKeepDefaults();
    if (data.missing_skills?.length) data.missing_skills.forEach(s => addSuggestion(`Add missing JD skill: ${s}`));

    // --- AI Feedback ---
    /*const aiText = data.ai_feedback || "AI feedback unavailable at the moment.";
    aiFeedbackEl.innerText = aiText;*/
    const aiText = data.ai_feedback;
    const sections = parseAIFeedbackToSections(aiText);
    fillStrengthsWeaknesses(sections.strengths, sections.weaknesses);
    if (sections.suggestions?.length) sections.suggestions.forEach(s => addSuggestion(s));

  } catch (err) {
    console.error("Analyze error:", err);
    alert("Error analyzing resume: " + (err.message || err));
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.innerText = "Analyze Resume";
  }
});
