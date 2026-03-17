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

def calculate_smart_ats(resume_text, job_description):
    resume_text = resume_text.lower()
    job_description = job_description.lower()

    jd_skills = extract_skills(job_description)
    resume_skills = extract_skills(resume_text)
    matched_skills = [s for s in resume_skills if s in jd_skills]
    missing_skills = [s for s in jd_skills if s not in resume_skills]
    skill_score = (len(matched_skills) / len(jd_skills) * 100) if jd_skills else 0

    exp_keywords = ['developer', 'engineer', 'manager', 'analyst', 'intern', 'associate', 'specialist']
    jd_roles = [word for word in job_description.split() if word in exp_keywords]
    resume_roles = [word for word in resume_text.split() if word in exp_keywords]
    role_matches = [r for r in resume_roles if r in jd_roles]
    experience_score = min(len(role_matches) / len(jd_roles) * 100 if jd_roles else 0, 100)

    edu_keywords = ['b.tech', 'b.e', 'm.tech', 'bachelor', 'master', 'msc', 'phd', 'degree']
    edu_score = 100 if any(k in resume_text for k in edu_keywords) else 0

    jd_keywords = [w for w in job_description.split() if w not in jd_skills]
    jd_kw_matches = [w for w in jd_keywords if w in resume_text]
    keyword_score = (len(jd_kw_matches) / len(jd_keywords) * 100) if jd_keywords else 0

    ats_score = round(
        0.5 * skill_score +
        0.2 * experience_score +
        0.2 * edu_score +
        0.1 * keyword_score,
        2
    )

    return ats_score, matched_skills, missing_skills
