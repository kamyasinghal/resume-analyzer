from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enables CORS for all routes

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Simple GET route to verify backend is running
@app.route('/', methods=['GET'])
def home():
    return "Resume Analyzer Backend is running!"

# POST route for resume analysis
@app.route('/analyze', methods=['POST'])
def analyze_resume():
    # Check if a file was uploaded
    file = request.files.get('resume', None)
    job_description = request.form.get('job_description', None)

    if not file and not job_description:
        return jsonify({'error': 'No resume or job description provided'}), 400

    filename = None
    if file:
        filename = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filename)

    # Dummy analysis (replace with actual parsing logic later)
    analysis = {
        'filename': file.filename if file else None,
        'skills': ['Python', 'Flask', 'HTML/CSS'],
        'experience': '2 years',
        'education': 'B.Tech CSE',
        'job_description_received': job_description if job_description else None
    }

    return jsonify(analysis)

if __name__ == '__main__':
    app.run(debug=True)
