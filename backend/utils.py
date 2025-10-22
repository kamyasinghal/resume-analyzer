# utils.py
import re

TECHNICAL_SKILLS = [
    "python", "java", "c++", "html", "css", "javascript", "flask", "django", "sql",
    "mysql", "mongodb", "react", "node.js", "machine learning", "data analysis", "git"
]

SOFT_SKILLS = [
    "communication", "leadership", "teamwork", "problem solving", "creativity",
    "adaptability", "critical thinking", "time management"
]

EDUCATION_KEYWORDS = [
    "b.tech", "be", "b.e.", "bsc", "msc", "m.tech", "mba", "phd"
]

def extract_skills(text):
    text = text.lower()
    found = set()
    for skill in TECHNICAL_SKILLS + SOFT_SKILLS:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text):
            found.add(skill)
    return list(found)

def extract_experience(text):
    text = text.lower()
    # Match patterns like "2 years", "3+ yrs", "5 yrs", "over 4 years"
    patterns = [
        r'(\d+)\+?\s*(years|yrs)',
        r'over\s+(\d+)\s*(years|yrs)',
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            return match.group(0)
    return "Not detected"

def extract_education(text):
    text = text.lower()
    for edu in EDUCATION_KEYWORDS:
        if edu in text:
            return edu.upper().replace('.', '')
    return "Not detected"

def calculate_ats_score(resume_text, job_description):
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_description)
    matches = [skill for skill in resume_skills if skill in job_skills]
    score = (len(matches) / len(job_skills) * 100) if job_skills else 0
    missing_skills = [skill for skill in job_skills if skill not in resume_skills]
    return round(score,2), matches, missing_skills
