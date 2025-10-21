async function analyzeResume(event) {
  if (event) event.preventDefault(); // Prevent page reload if inside a form

  const jobDescription = document.getElementById("jobDescription").value;
  const resumeFile = document.getElementById("resumeUpload").files[0];

  if (!resumeFile && !jobDescription) {
    alert("Please upload a resume or paste a job description.");
    return;
  }

  const formData = new FormData();
  if (resumeFile) formData.append("resume", resumeFile);
  if (jobDescription) formData.append("job_description", jobDescription);

  const response = await fetch("http://127.0.0.1:5000/analyze", {
    method: "POST",
    body: formData
  });

  const data = await response.json();
  document.getElementById("output").innerText = JSON.stringify(data, null, 2);

  // Show results section (example)
  document.getElementById("results").style.display = "block";
}
