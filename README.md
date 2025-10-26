# Smart Resume Analyzer
The Smart Resume Analyzer is a web-based tool designed to help job applicants evaluate their resumes against job descriptions. It combines keyword-based ATS scoring, experience and education extraction, and AI-driven feedback to provide actionable insights for improving resumes. The system is interactive and visually appealing, offering charts, strengths/weaknesses analysis, and suggestions for optimization.

# Key Features
1.  Resume Upload & Parsing : Drag & drop or browse to upload resumes in PDF or DOCX formats.
2.  Job Description Analysis : The system compares resume content against JD to detect matching skills, missing skills, and relevant keywords.
3.  ATS Score Calculation : Smart scoring based on: Skills match (50%), Experience relevance (20%), Education match (20%), Job description keyword relevance (10%)
4.  Skills Detection : Detects technical and soft skills mentioned in the resume.
5.  Experience & Education Extraction : Extracts roles, companies, durations and education from the resume.
6.  Strengths & Weaknesses Analysis : Uses gemini API to review the resume and highlight strengths and weaknesses.
7.  Interactive Dashboard : Visualizes ATS Score, Skills and shows suggestions dynamically.
8.  AI Insights: AI generates actionable feedback, including: Resume structure improvements, Keyword enhancement, Achievement highlighting


# Tech Stack

Frontend:
>HTML/CSS/JS — responsive UI and charts
>Chart.js — for ATS score and skill visualization
>Dynamic dashboard with real-time updates

Backend:
>Python + Flask — server and REST API
>Flask-CORS — cross-origin requests
>PyPDF2 & python-docx — document parsing
>Werkzeug — secure file handling
>Dotenv — manage API keys securely

AI Integration:
>Google Gemini API — for strengths/weaknesses and suggestions

Utilities:
>Regex-based skill, experience, and education extraction
>Advanced smart ATS scoring algorithm (weighted scoring system)

File Handling:
>Uploaded resumes stored temporarily in uploads/ folder
>Allowed formats: .pdf and .docx

# What Users Can Do

Upload resumes and get instant ATS scores.
Detect skills gaps vs job description.
View concise experience & education summary.
Receive AI-generated actionable feedback.
Visualize skills distribution and ATS score with charts.
Get improvement suggestions to optimize resumes for recruiter systems.

# Live Snapshot 
(host on local server)
<img width="1905" height="1030" alt="image" src="https://github.com/user-attachments/assets/c57e6c94-0ac3-4774-a672-cc216fc53864" />
<img width="1814" height="975" alt="image" src="https://github.com/user-attachments/assets/f9240580-487a-4e48-af71-5d5c17969e21" />
<img width="1919" height="965" alt="image" src="https://github.com/user-attachments/assets/9b409feb-fa07-474d-9eac-256e8a4e7bcd" />
