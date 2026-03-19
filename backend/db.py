import os
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    url = os.getenv("MYSQL_URL")
    if url:
        # Parse mysql://user:pass@host:port/dbname
        from urllib.parse import urlparse
        p = urlparse(url)
        return pymysql.connect(
            host=p.hostname,
            port=p.port or 3306,
            user=p.username,
            password=p.password,
            database=p.path.lstrip('/'),
            cursorclass=DictCursor,
            autocommit=True
        )
    # Fallback to individual env vars
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DB", "resumeiq"),
        cursorclass=DictCursor,
        autocommit=True
    )

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS User (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            email       VARCHAR(255) UNIQUE,
            name        VARCHAR(255),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Company (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            name        VARCHAR(255) NOT NULL,
            industry    VARCHAR(255),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Job (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            company_id   INT,
            title        VARCHAR(255),
            description  TEXT,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES Company(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Resume (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            user_id      INT,
            filename     VARCHAR(255),
            file_type    VARCHAR(10),
            raw_text     LONGTEXT,
            uploaded_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES User(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Skill (
            id    INT AUTO_INCREMENT PRIMARY KEY,
            name  VARCHAR(100) UNIQUE NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Resume_Skill (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            resume_id  INT NOT NULL,
            skill_id   INT NOT NULL,
            matched    BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (resume_id) REFERENCES Resume(id),
            FOREIGN KEY (skill_id)  REFERENCES Skill(id),
            UNIQUE KEY uq_resume_skill (resume_id, skill_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Matches (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            resume_id    INT NOT NULL,
            job_id       INT,
            match_score  FLOAT NOT NULL,
            matched_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resume_id) REFERENCES Resume(id),
            FOREIGN KEY (job_id)    REFERENCES Job(id)
        )
    """)

    cur.close()
    conn.close()
    print("Database tables initialised.")


def save_resume(filename, file_type, raw_text):
    """Insert a resume row and return its new ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO Resume (filename, file_type, raw_text) VALUES (%s, %s, %s)",
        (filename, file_type, raw_text)
    )
    resume_id = cur.lastrowid
    cur.close()
    conn.close()
    return resume_id


def save_skills(resume_id, matched_skills, missing_skills):
    """Upsert skills and link them to the resume."""
    conn = get_connection()
    cur = conn.cursor()

    all_skills = [(s, True) for s in matched_skills] + [(s, False) for s in missing_skills]

    for skill_name, is_matched in all_skills:
        # Upsert skill
        cur.execute(
            "INSERT INTO Skill (name) VALUES (%s) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)",
            (skill_name,)
        )
        skill_id = cur.lastrowid

        # Link to resume
        cur.execute("""
            INSERT INTO Resume_Skill (resume_id, skill_id, matched)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE matched=%s
        """, (resume_id, skill_id, is_matched, is_matched))

    cur.close()
    conn.close()


def save_match(resume_id, match_score, job_description=None):
    """Store the ATS match score, optionally linking a job."""
    conn = get_connection()
    cur = conn.cursor()

    job_id = None
    if job_description and job_description.strip():
        # Save as anonymous job if no real job exists
        cur.execute(
            "INSERT INTO Job (title, description) VALUES (%s, %s)",
            ("Uploaded JD", job_description[:2000])
        )
        job_id = cur.lastrowid

    cur.execute(
        "INSERT INTO Matches (resume_id, job_id, match_score) VALUES (%s, %s, %s)",
        (resume_id, job_id, match_score)
    )

    cur.close()
    conn.close()
