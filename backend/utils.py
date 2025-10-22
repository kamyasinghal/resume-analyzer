# utils.py

TECHNICAL_SKILLS = [
    "python", "java", "c++", "javascript", "flask", "django", 
    "html", "css", "react", "sql", "mongodb", "aws", "git"
]

SOFT_SKILLS = [
    "communication", "leadership", "teamwork", "problem solving", 
    "adaptability", "creativity", "time management"
]

def extract_skills(text):
    """
    Returns a list of detected skills from resume text.
    """
    text = text.lower()
    detected = [skill for skill in TECHNICAL_SKILLS + SOFT_SKILLS if skill in text]
    return detected

def calculate_ats_score(resume_text, job_description):
    """
    Simple ATS score = percentage of JD keywords found in resume
    """
    if not job_description:
        return 0
    resume_text = resume_text.lower()
    jd_keywords = job_description.lower().split()
    matched = sum(1 for word in jd_keywords if word in resume_text)
    return int((matched / len(jd_keywords)) * 100)
