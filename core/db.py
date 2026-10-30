import sqlite3
import json
from datetime import datetime
from pathlib import Path
from core.config import settings

def get_connection():
    db_path = Path(settings.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Profiles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT DEFAULT 'کاربر هوشمند',
        target_title TEXT DEFAULT 'تحلیل‌گر داده / Data Analyst',
        raw_resume TEXT,
        parsed_skills TEXT DEFAULT '[]',
        ats_score INTEGER DEFAULT 0,
        improvement_tips TEXT DEFAULT '[]',
        missing_trend_skills TEXT DEFAULT '[]',
        target_city TEXT DEFAULT 'تهران',
        golden_hour_enabled INTEGER DEFAULT 1,
        match_threshold INTEGER DEFAULT 70,
        daily_cap INTEGER DEFAULT 15,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. Jobs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT UNIQUE,
        platform TEXT,
        title TEXT,
        company TEXT,
        location TEXT,
        salary_range TEXT,
        url TEXT,
        description TEXT,
        skills_required TEXT DEFAULT '[]',
        match_score INTEGER DEFAULT 0,
        match_reasons TEXT DEFAULT '[]',
        missing_skills TEXT DEFAULT '[]',
        status TEXT DEFAULT 'discovered',
        tracking_code TEXT,
        applied_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 3. Interviews Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT,
        job_title TEXT,
        company TEXT,
        question TEXT,
        user_answer TEXT,
        score INTEGER DEFAULT 0,
        feedback TEXT,
        sample_ideal_answer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. Ad Banners & Promotions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS banners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        subtitle TEXT,
        badge TEXT,
        cta_text TEXT,
        cta_link TEXT,
        banner_type TEXT DEFAULT 'promo',
        is_active INTEGER DEFAULT 1
    );
    """)

    # 5. Accounts & Credentials Table (Jobinja, Jobvision)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT UNIQUE,
        username_or_email TEXT,
        password TEXT,
        phone_number TEXT,
        session_cookies TEXT DEFAULT '{}',
        status TEXT DEFAULT 'not_configured',
        last_login_at TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 6. Live Execution Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS execution_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name TEXT,
        log_type TEXT DEFAULT 'info',
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 7. User-Specific Job Matches & Applications (Multi-User Data Segregation)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        job_id TEXT NOT NULL,
        match_score INTEGER DEFAULT 0,
        match_reasons TEXT DEFAULT '[]',
        missing_skills TEXT DEFAULT '[]',
        status TEXT DEFAULT 'discovered',
        tracking_code TEXT,
        applied_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, job_id)
    );
    """)
    
    # Insert default profile if not exists
    cursor.execute("SELECT COUNT(*) FROM profiles")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO profiles (full_name, target_title, target_city, golden_hour_enabled, match_threshold, daily_cap)
        VALUES ('کاربر آزمایشی', 'دیتا آنالیست / Data Analyst', 'تهران', 1, 70, 15)
        """)

    # Insert default accounts for Jobinja and Jobvision if not exists
    cursor.execute("SELECT COUNT(*) FROM accounts")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO accounts (platform, username_or_email, status)
        VALUES 
        ('jobinja', 'demo@jobinja.ir', 'not_configured'),
        ('jobvision', '09120000000', 'not_configured')
        """)
        
    # Insert default promo banner if not exists
    cursor.execute("SELECT COUNT(*) FROM banners")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO banners (title, subtitle, badge, cta_text, cta_link, banner_type)
        VALUES 
        ('اشتراک ویژه Co-Pilot حرفه‌ای', 'دسترسی نامحدود به ارسال خودکار روزانه در ساعت طلایی و شبیه‌ساز نامحدود مصاحبه هوشمند', 'تخفیف ویژه ۴۰٪', 'خرید اشتراک ماهانه (۱۹۹ هزار تومان)', '#pricing', 'premium'),
        ('فرصت اسپانسری استارتاپ‌ها', 'آگهی استخدام شرکت خود را در صدر ویترین هزاران کارجوی متخصص قرار دهید', 'همکاری تجاری', 'ثبت آگهی ویژه کارفرما', '#sponsor', 'sponsor')
        """)

    conn.commit()
    conn.close()

def get_user_job_stats(user_id: int) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM user_jobs WHERE user_id = ? AND status = 'applied'", (user_id,))
    total_applied = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM user_jobs WHERE user_id = ? AND status = 'queued_golden_hour'", (user_id,))
    golden_hour_queue = cursor.fetchone()[0]
    conn.close()
    return {
        "total_jobs": total_jobs,
        "total_applied": total_applied,
        "golden_hour_queue": golden_hour_queue
    }

def get_user_jobs_list(user_id: int, limit: int = 10) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        j.id, j.job_id, j.platform, j.title, j.company, j.location, j.salary_range, j.url, j.description, j.skills_required,
        COALESCE(uj.match_score, 0) as match_score,
        COALESCE(uj.match_reasons, '[]') as match_reasons,
        COALESCE(uj.missing_skills, '[]') as missing_skills,
        COALESCE(uj.status, 'discovered') as status,
        uj.tracking_code,
        uj.applied_at
    FROM jobs j
    LEFT JOIN user_jobs uj ON j.job_id = uj.job_id AND uj.user_id = ?
    ORDER BY uj.match_score DESC, j.id DESC
    LIMIT ?
    """, (user_id, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def upsert_user_job(user_id: int, job_id: str, match_score: int, match_reasons: list, missing_skills: list, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO user_jobs (user_id, job_id, match_score, match_reasons, missing_skills, status, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id, job_id) DO UPDATE SET
        match_score = excluded.match_score,
        match_reasons = excluded.match_reasons,
        missing_skills = excluded.missing_skills,
        status = CASE WHEN user_jobs.status = 'applied' THEN 'applied' ELSE excluded.status END,
        updated_at = excluded.updated_at
    """, (
        user_id, job_id, match_score,
        json.dumps(match_reasons, ensure_ascii=False),
        json.dumps(missing_skills, ensure_ascii=False),
        status, now
    ))
    conn.commit()
    conn.close()

def apply_user_job(user_id: int, job_id: str, tracking_code: str):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO user_jobs (user_id, job_id, status, tracking_code, applied_at, updated_at)
    VALUES (?, ?, 'applied', ?, ?, ?)
    ON CONFLICT(user_id, job_id) DO UPDATE SET
        status = 'applied',
        tracking_code = excluded.tracking_code,
        applied_at = excluded.applied_at,
        updated_at = excluded.updated_at
    """, (user_id, job_id, tracking_code, now, now))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database updated and initialized successfully.")
