document.getElementById("resumeForm").addEventListener("submit", analyzeResume);

async function analyzeResume(event) {
    event.preventDefault(); // MUST prevent default form submission

    const resumeFile = document.getElementById("resumeUpload").files[0];
    const jobDescription = document.getElementById("jobDescription").value;

    const formData = new FormData();
    if (resumeFile) formData.append("resume", resumeFile);
    if (jobDescription) formData.append("job_description", jobDescription);

    const outputDiv = document.getElementById("output");
    const analyzeBtn = document.getElementById("analyzeBtn");
    
    // Loading state
    analyzeBtn.disabled = true;
    analyzeBtn.innerText = "Analyzing...";
    outputDiv.innerText = "Processing...";

    try {
        const response = await fetch("http://127.0.0.1:5000/analyze", {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        outputDiv.innerText = JSON.stringify(data, null, 2);
    } catch (err) {
        console.error(err);
        outputDiv.innerText = `Error: ${err.message}`;
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.innerText = "Analyze Resume";
    }
}
