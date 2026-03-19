import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import tempfile
from werkzeug.utils import secure_filename
from utils import extract_skills, calculate_smart_ats
from PyPDF2 import PdfReader
import docx
import google.generativeai as genai
from dotenv import load_dotenv
import re

# DB import — fail gracefully if DB not configured
try:
    from db import init_db, save_resume, save_skills, save_match
    DB_ENABLED = True
except Exception as e:
    print("DB not available:", e)
    DB_ENABLED = False

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))
CORS(app)
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

# Init DB tables on startup
if DB_ENABLED:
    try:
        init_db()
    except Exception as e:
        print("DB init error:", e)
        DB_ENABLED = False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path):
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
    match = re.search(r'(WORK EXPERIENCE|Professional Experience|Experience)(.*?)(EDUCATION|$)', text, re.IGNORECASE | re.DOTALL)
    exp_text = match.group(2) if match else text
    lines = [line.strip() for line in exp_text.split('\n') if line.strip()]
    jobs = []
    current_job = {}
    for line in lines:
        dur_match = re.search(r'(\b\d{4}\b.*?Present|\b\d{4}\b.*?\b\d{4}\b|\d+\+?\s*years?)', line, re.IGNORECASE)
        if dur_match:
            current_job['duration'] = dur_match.group(0).strip()
            if 'title' in current_job:
                jobs.append(current_job)
                current_job = {}
            continue
        title_match = re.search(r'([A-Z][a-zA-Z &]+(?:Engineer|Developer|Manager|Lead|Consultant|Intern))', line)
        if title_match:
            current_job['title'] = title_match.group(0).strip()
            continue
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
    edu_keywords = ["B.Tech", "B.E", "Bachelor", "Master", "M.Tech", "BSc", "MSc", "PhD", "University", "College", "Degree", "Diploma"]
    lines = [line.strip() for line in text.split("\n") if any(k.lower() in line.lower() for k in edu_keywords)]
    return lines[:2] if lines else ["Education details not found"]

def get_ai_feedback(resume_text, job_description):
    if not model:
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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    try:
        resume_text = ""
        job_description = request.form.get("job_description", "")
        original_filename = "resume"
        file_type = "unknown"

        if 'resume' in request.files:
            file = request.files['resume']
            if file and allowed_file(file.filename):
                original_filename = secure_filename(file.filename)
                file_type = original_filename.rsplit('.', 1)[1].lower()
                tmp_dir = tempfile.gettempdir()
                file_path = os.path.join(tmp_dir, original_filename)
                file.save(file_path)
                resume_text = extract_text_from_file(file_path)
                try:
                    os.remove(file_path)
                except Exception:
                    pass

        if not resume_text:
            return jsonify({"error": "No text found in resume."}), 400

        ats_score, matched_skills, missing_skills = calculate_smart_ats(resume_text, job_description)
        experience_summary = extract_experience(resume_text)
        education_summary  = extract_education(resume_text)
        ai_feedback        = get_ai_feedback(resume_text, job_description)

        # ── Save to database ──────────────────────────
        resume_id = None
        if DB_ENABLED:
            try:
                resume_id = save_resume(original_filename, file_type, resume_text)
                save_skills(resume_id, matched_skills, missing_skills)
                save_match(resume_id, ats_score, job_description)
            except Exception as db_err:
                print("DB save error:", db_err)
        # ─────────────────────────────────────────────

        return jsonify({
            "skills":        matched_skills,
            "missing_skills": missing_skills,
            "experience":    experience_summary,
            "education":     education_summary,
            "ats_score":     ats_score,
            "ai_feedback":   ai_feedback,
            "resume_id":     resume_id
        })

    except Exception as e:
        print("Error in /analyze:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
```

---

### 3. Update `requirements.txt` (repo root)
```
Flask==3.1.2
flask-cors==5.0.0
Werkzeug==3.1.3
PyPDF2==3.0.1
python-docx==1.1.2
google-generativeai
python-dotenv==1.0.1
Jinja2==3.1.6
PyMySQL==1.1.1
cryptography==42.0.8
```

---

### 4. Add `MYSQL_URL` to Vercel environment variables

Once you have your Railway MySQL URL, go to **Vercel → Project → Settings → Environment Variables** and add:
```
MYSQL_URL = mysql://user:password@host.railway.internal:3306/railway
```

---

### How the data flows
```
User uploads resume
       ↓
Resume table  ← filename, file_type, raw_text
       ↓
Skill table   ← upsert each skill name
       ↓
Resume_Skill  ← links resume ↔ skill, marks matched=true/false
       ↓
Job table     ← stores the pasted job description
       ↓
Matches table ← resume_id, job_id, match_score, timestamp
