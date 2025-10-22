from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Render homepage
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')  # <- Flask loads from templates/

# /analyze POST route (keep your existing code)
@app.route('/analyze', methods=['POST'])
def analyze_resume():
    file = request.files.get('resume')
    job_description = request.form.get('job_description')

    if not file and not job_description:
        return jsonify({'error': 'No resume or job description provided'}), 400

    filename = None
    if file and allowed_file(file.filename):
        safe_filename = secure_filename(file.filename)
        filename = os.path.join(UPLOAD_FOLDER, safe_filename)
        file.save(filename)

    analysis = {
        'filename': file.filename if file else None,
        'skills': ['Python', 'Flask', 'HTML/CSS', 'JavaScript', 'SQL'],
        'experience': '2 years',
        'education': 'B.Tech CSE',
        'job_description_received': job_description if job_description else None,
        'overall_score': 85,
        'experience_summary': "Worked as Software Developer at XYZ Corp.",
        'format_analysis': "Well-structured sections, clear headings.",
        'keywords': "Contains industry keywords: Python, Flask, SQL",
        'suggestions': "Add more projects, highlight certifications."
    }

    return jsonify(analysis)

if __name__ == '__main__':
    app.run(debug=True)
