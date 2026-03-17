import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))

@app.route('/')
def home():
    errors = []
    
    try:
        from flask_cors import CORS
    except Exception as e:
        errors.append(f"flask_cors: {e}")

    try:
        from PyPDF2 import PdfReader
    except Exception as e:
        errors.append(f"PyPDF2: {e}")

    try:
        import docx
    except Exception as e:
        errors.append(f"docx: {e}")

    try:
        import google.generativeai as genai
    except Exception as e:
        errors.append(f"google.generativeai: {e}")

    try:
        from utils import extract_skills, calculate_smart_ats
    except Exception as e:
        errors.append(f"utils: {e}")

    if errors:
        return jsonify({"import_errors": errors}), 200
    return jsonify({"status": "all imports OK"})

if __name__ == "__main__":
    app.run(debug=True)
