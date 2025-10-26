from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from utils import extract_skills, calculate_smart_ats
from PyPDF2 import PdfReader
import docx
import google.generativeai as genai
from dotenv import load_dotenv
import re

# ---------------- Flask Setup ----------------
app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# ---------------- Gemini Setup ----------------
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------- Helper Functions ----------------

def extract_text_from_file(file_path):
    """Extract text from PDF or DOCX file."""
    text = ""
    if file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() or ""
    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    return text.strip()


def extract_experience(text):
    """
    Extract short, structured experience summary:
    Returns first 2 roles with title, company, and duration.
    """
    # Look for WORK EXPERIENCE section first
    match = re.search(r'(WORK EXPERIENCE|Professional Experience|Experience)(.*?)(EDUCATION|$)', text, re.IGNORECASE | re.DOTALL)
    exp_text = match.group(2) if match else text

    lines = [line.strip() for line in exp_text.split('\n') if line.strip()]
    jobs = []
    current_job = {}

    for line in lines:
        # Duration pattern
        dur_match = re.search(r'(\b\d{4}\b.*?Present|\b\d{4}\b.*?\b\d{4}\b|\d+\+?\s*years?)', line, re.IGNORECASE)
        if dur_match:
            current_job['duration'] = dur_match.group(0).strip()
            if 'title' in current_job:
                jobs.append(current_job)
                current_job = {}
            continue

        # Title pattern
        title_match = re.search(r'([A-Z][a-zA-Z &]+(?:Engineer|Developer|Manager|Lead|Consultant|Intern))', line)
        if title_match:
            current_job['title'] = title_match.group(0).strip()
            continue

        # Company pattern
        if 'title' in current_job and 'company' not in current_job:
            current_job['company'] = line.strip()

    if current_job.get('title'):
        jobs.append(current_job)

    summaries = []
    for j in jobs[:2]:
        parts = [j.get('title', ''), j.get('company', ''), j.get('duration', '')]
        summaries.append(' at '.join([p for p in parts[:2] if p]) + (f" ({parts[2]})" if parts[2] else ""))

    return summaries if summaries else ["Experience not clearly mentioned"]


def extract_education(text):
    """Extract first relevant education degree."""
    edu_keywords = ["B.Tech", "B.E", "Bachelor", "Master", "M.Tech", "BSc", "MSc", "PhD", "University", "College", "Degree", "Diploma"]
    lines = [line.strip() for line in text.split("\n") if any(k.lower() in line.lower() for k in edu_keywords)]
    return lines[:2] if lines else ["Education details not found"]


def get_ai_feedback(resume_text, job_description):
    """Gemini feedback for strengths, weaknesses, and suggestions only."""
    prompt = f"""
You are an expert HR reviewer.
Compare the resume against the job description.

Return exactly 3 Strengths, 3 Weaknesses, and 3 Suggestions in this format:

Strengths:
- [item 1]
- [item 2]
- [item 3]

Weaknesses:
- [item 1]
- [item 2]
- [item 3]

Suggestions:
- [item 1]
- [item 2]
- [item 3]

Resume:
{resume_text[:3000]}

Job Description:
{job_description[:1000]}
"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print("Gemini Error:", e)
        # fallback example
        return """
Strengths:
- Clear structure
- Good technical foundation
- Organized formatting

Weaknesses:
- Limited achievements listed
- Generic summary
- Needs stronger keywords

Suggestions:
- Add measurable results
- Customize resume for job description
- Include certifications or internships
"""

# ---------------- Routes ----------------

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze_resume():
    try:
        resume_text = ""
        job_description = request.form.get("job_description", "")

        # File processing
        if 'resume' in request.files:
            file = request.files['resume']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                resume_text = extract_text_from_file(file_path)

        if not resume_text:
            return jsonify({"error": "No text found in resume."}), 400

        # --- Feature Extraction ---
        ats_score, matched_skills, missing_skills = calculate_smart_ats(resume_text, job_description)
        experience_summary = extract_experience(resume_text)
        education_summary = extract_education(resume_text)
        ai_feedback = get_ai_feedback(resume_text, job_description)

        return jsonify({
            "skills": matched_skills,
            "missing_skills": missing_skills,
            "experience": experience_summary,
            "education": education_summary,
            "ats_score": ats_score,
            "ai_feedback": ai_feedback
        })

    except Exception as e:
        print("Error in /analyze:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
