from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from utils import extract_skills, calculate_ats_score

# PDF & DOCX
from PyPDF2 import PdfReader
import docx

# Flask setup
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html') 


def parse_resume(file_path):
    ext = file_path.rsplit('.', 1)[1].lower()
    text = ""
    if ext == "pdf":
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() + " "
    elif ext == "docx":
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + " "
    return text

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    file = request.files.get('resume')
    job_description = request.form.get('job_description', "")

    if not file:
        return jsonify({'error': 'No resume uploaded'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Upload PDF or DOCX only.'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    resume_text = parse_resume(filepath)
    skills_detected = extract_skills(resume_text)
    ats_score = calculate_ats_score(resume_text, job_description)

    # Dummy experience and education (can improve later with NLP)
    experience = "2 years"
    education = "B.Tech CSE"

    return jsonify({
        "filename": file.filename,
        "skills": skills_detected,
        "experience": experience,
        "education": education,
        "ats_score": ats_score
    })

if __name__ == '__main__':
    app.run(debug=True)
