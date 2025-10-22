const uploadArea = document.getElementById("uploadArea");
const resumeUpload = document.getElementById("resumeUpload");
const uploadBtn = document.getElementById("uploadBtn");
const fileNameSpan = document.getElementById("fileName");
const analyzeBtn = document.getElementById("analyzeBtn");

// Upload button
uploadBtn.addEventListener("click", () => resumeUpload.click());

// Drag & Drop
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

// Show file name
resumeUpload.addEventListener("change", () => {
  if (resumeUpload.files.length)
    fileNameSpan.textContent = resumeUpload.files[0].name;
});

// Analyze Resume
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
    const data = await res.json();

    document.getElementById("skills").innerText = data.skills.join(", ");
    document.getElementById("experience").innerText = data.experience;
    document.getElementById("education").innerText = data.education;
    document.getElementById("dashboard").style.display = "block";

    // Animate ATS Score
    const ctx1 = document.getElementById("overallScoreChart").getContext("2d");
    let score = 0;
    const targetScore = data.ats_score; //real ATS score from backend
    const scoreText = document.getElementById("scoreText");

    const chart = new Chart(ctx1, {
      type: "doughnut",
      data: {
        labels: ["Score", "Remaining"],
        datasets: [{
          data: [0, 100],
          backgroundColor: ["#0D9488", "#F0FDFA"],
          borderWidth: 0
        }]
      },
      options: {
        cutout: "75%",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
      }
    });

    const interval = setInterval(() => {
      if (score >= targetScore) clearInterval(interval);
      else score++;
      chart.data.datasets[0].data = [score, 100 - score];
      chart.update();
      scoreText.innerText = `${score}%`;
    }, 20);

    // Skills chart
    const ctx2 = document.getElementById("skillsChart").getContext("2d");
    new Chart(ctx2, {
      type: "doughnut",
      data: {
        labels: ["Python", "Flask", "HTML/CSS"],
        datasets: [{
          data: [5, 3, 2],
          backgroundColor: ["#0D9488", "#F97316", "#06B6D4"],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: { legend: { position: "bottom" } }
      }
    });

  } catch (err) {
    console.error(err);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.innerText = "Analyze Resume";
  }
});
