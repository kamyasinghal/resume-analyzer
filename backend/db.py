import os
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    url = os.getenv("MYSQL_URL")
    if url:
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

    # USER — matches ER diagram exactly
    cur.execute("""
        CREATE TABLE IF NOT EXISTS User (
            user_id     INT AUTO_INCREMENT PRIMARY KEY,
            name        VARCHAR(255),
            role        VARCHAR(50),
            email       VARCHAR(255) UNIQUE,
            phone       VARCHAR(20),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # COMPANY — matches ER diagram exactly
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Company (
            company_id  INT AUTO_INCREMENT PRIMARY KEY,
            name        VARCHAR(255) NOT NULL,
            location    VARCHAR(255),
            industry    VARCHAR(255),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # JOB — matches ER diagram exactly
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Job (
            job_id               INT AUTO_INCREMENT PRIMARY KEY,
            company_id           INT,
            job_title            VARCHAR(255),
            required_experience  VARCHAR(100),
            job_description      TEXT,
            posted_date          DATE,
            created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES Company(company_id)
        )
    """)

    # RESUME — matches ER diagram exactly
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Resume (
            resume_id   INT AUTO_INCREMENT PRIMARY KEY,
            user_id     INT,
            title       VARCHAR(255),
            experience  VARCHAR(100),
            summary     TEXT,
            education   VARCHAR(255),
            filename    VARCHAR(255),
            file_type   VARCHAR(10),
            raw_text    LONGTEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES User(user_id)
        )
    """)

    # SKILL — matches ER diagram exactly
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Skill (
            skill_id    INT AUTO_INCREMENT PRIMARY KEY,
            skill_name  VARCHAR(100) UNIQUE NOT NULL,
            category    VARCHAR(100)
        )
    """)

    # RESUME_SKILL (Has_Skill M:N) — matches ER diagram exactly
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Resume_Skill (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            resume_id   INT NOT NULL,
            skill_id    INT NOT NULL,
            proficiency VARCHAR(50),
            matched     BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (resume_id) REFERENCES Resume(resume_id),
            FOREIGN KEY (skill_id)  REFERENCES Skill(skill_id),
            UNIQUE KEY uq_resume_skill (resume_id, skill_id)
        )
    """)

    # APPLICATION (Applies_To M:N) — matches ER diagram exactly
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Application (
            application_id  INT AUTO_INCREMENT PRIMARY KEY,
            resume_id       INT NOT NULL,
            job_id          INT NOT NULL,
            status          VARCHAR(20) DEFAULT 'APPLIED',
            applied_date    DATE,
            FOREIGN KEY (resume_id) REFERENCES Resume(resume_id),
            FOREIGN KEY (job_id)    REFERENCES Job(job_id)
        )
    """)

    # MATCHES — for ATS score storage
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Matches (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            resume_id   INT NOT NULL,
            job_id      INT,
            match_score FLOAT NOT NULL,
            matched_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resume_id) REFERENCES Resume(resume_id),
            FOREIGN KEY (job_id)    REFERENCES Job(job_id)
        )
    """)

    cur.close()
    conn.close()
    print("Database tables initialised.")


def save_resume(filename, file_type, raw_text):
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
    conn = get_connection()
    cur = conn.cursor()

    all_skills = [(s, True) for s in matched_skills] + [(s, False) for s in missing_skills]

    for skill_name, is_matched in all_skills:
        cur.execute(
            "INSERT INTO Skill (skill_name) VALUES (%s) ON DUPLICATE KEY UPDATE skill_id=LAST_INSERT_ID(skill_id)",
            (skill_name,)
        )
        skill_id = cur.lastrowid

        cur.execute("""
            INSERT INTO Resume_Skill (resume_id, skill_id, matched)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE matched=%s
        """, (resume_id, skill_id, is_matched, is_matched))

    cur.close()
    conn.close()


def save_match(resume_id, match_score, job_description=None):
    conn = get_connection()
    cur = conn.cursor()

    job_id = None
    if job_description and job_description.strip():
        cur.execute(
            "INSERT INTO Job (job_title, job_description) VALUES (%s, %s)",
            ("Uploaded JD", job_description[:2000])
        )
        job_id = cur.lastrowid

    cur.execute(
        "INSERT INTO Matches (resume_id, job_id, match_score) VALUES (%s, %s, %s)",
        (resume_id, job_id, match_score)
    )

    cur.close()
    conn.close()
