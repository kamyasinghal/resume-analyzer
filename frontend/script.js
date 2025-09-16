document.getElementById("analyzeBtn").addEventListener("click", function() {
  const jobDesc = document.getElementById("jobDescription").value;
  const resumeFile = document.getElementById("resumeUpload").files[0];

  if (!resumeFile || !jobDesc) {
    alert("Please upload a resume and enter job description!");
    return;
  }

  // For now: just show dummy results
  document.getElementById("results").style.display = "block";
  document.getElementById("score").innerText = "ATS Score: 72%";

  const ctx = document.getElementById("chart").getContext("2d");
  new Chart(ctx, {
    type: "pie",
    data: {
      labels: ["Matched Keywords", "Missing Keywords"],
      datasets: [{
        data: [18, 7],
        backgroundColor: ["#4CAF50", "#f44336"]
      }]
    }
  });

  document.getElementById("feedback").innerHTML = `
    <h3>AI Feedback:</h3>
    <ul>
      <li>✅ Good technical skills listed</li>
      <li>⚠️ Missing leadership experience</li>
      <li>⚠️ No mention of teamwork projects</li>
    </ul>
  `;
});
