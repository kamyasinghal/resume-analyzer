from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from utils import extract_skills, calculate_ats_score, extract_experience, extract_education
from PyPDF2 import PdfReader
import docx
import google.generativeai as genai
from dotenv import load_dotenv

# Flask setup
app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load Gemini API key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

ALLOWED_EXTENSIONS = {'pdf', 'docx'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

# Extract text from uploaded file
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

# Get AI feedback
def get_ai_feedback(resume_text, job_description):
    prompt = f"""
You are a professional resume reviewer. Analyze the resume below against the job description. 
Provide exactly 3 strengths, 3 weaknesses, and 3 suggestions.

Resume:
{resume_text[:3000]}

Job Description:
{job_description[:1000]}

Format your response EXACTLY as:

Strengths:
- [strength 1]
- [strength 2]
- [strength 3]

Weaknesses:
- [weakness 1]
- [weakness 2]
- [weakness 3]

Suggestions:
- [suggestion 1]
- [suggestion 2]
- [suggestion 3]
"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print("Gemini Error:", e)
        return """
Strengths:
- Strong problem solving
- Good teamwork
- Communication skills

Weaknesses:
- Needs more leadership experience
- Time management improvement
- Limited cloud experience

Suggestions:
- Highlight key projects
- Quantify achievements
- Add certifications
"""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    try:
        resume_text = ""
        job_description = request.form.get("job_description", "")

        # File upload
        if 'resume' in request.files:
            file = request.files['resume']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                resume_text = extract_text_from_file(file_path)

        if not resume_text:
            return jsonify({"error": "No text found in resume."}), 400

        # Extract features
        ats_score, matched_skills, missing_skills = calculate_ats_score(resume_text, job_description)
        experience = extract_experience(resume_text)
        education = extract_education(resume_text)
        ai_feedback = get_ai_feedback(resume_text, job_description)

        return jsonify({
            "skills": matched_skills,
            "missing_skills": missing_skills,
            "experience": experience,
            "education": education,
            "ats_score": ats_score,
            "ai_feedback": ai_feedback
        })
    except Exception as e:
        print("Error in /analyze:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
