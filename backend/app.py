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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    file = request.files.get('resume')
    job_description = request.form.get('job_description')

    if not file and not job_description:
        return jsonify({'error': 'No resume or job description provided'}), 400

    if file and not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Upload PDF or DOCX only.'}), 400

    if file:
        safe_filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, safe_filename))

    analysis = {
        'filename': file.filename if file else None,
        'skills': ['Python', 'Flask', 'HTML/CSS'],
        'experience': '2 years',
        'education': 'B.Tech CSE',
        'job_description_received': job_description
    }

    return jsonify(analysis)

if __name__ == '__main__':
    app.run(debug=True)
