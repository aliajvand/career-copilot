"""
Core Database Layer for Career Co-Pilot Enterprise.
Built with skills: db-schema-design + data-migration-alembic
Features:
- Composite indexing for fast queries on job_id, user_id, created_at
- Soft-delete support (is_deleted, deleted_at)
- Dedicated Audit Log table for security and compliance
- Transactions table for payment gateways with idempotency keys
- Application experiments table for A/B testing optimal apply hours
- Ready for SQLite and PostgreSQL migration
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
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
        is_deleted INTEGER DEFAULT 0,
        deleted_at TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. Jobs Table with Soft Delete and Indexes
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
        is_deleted INTEGER DEFAULT 0,
        deleted_at TIMESTAMP,
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
        rubric_breakdown TEXT DEFAULT '{}',
        hiring_recommendation TEXT,
        candidate_tier TEXT,
        candidate_consent INTEGER DEFAULT 1,
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

    # 5. Accounts & Credentials Table (Encrypted sessions)
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

    # 7. User-Specific Job Matches (Multi-User Data Segregation)
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
        requires_confirmation INTEGER DEFAULT 1,
        user_confirmed INTEGER DEFAULT 0,
        is_deleted INTEGER DEFAULT 0,
        deleted_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, job_id)
    );
    """)

    # 8. Audit Log Table (Compliance & OWASP security tracking)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT,
        changes_json TEXT DEFAULT '{}',
        ip_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 9. Payment Transactions Table (Zarinpal / IDPay / Telegram Stars)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        authority TEXT UNIQUE,
        amount INTEGER NOT NULL,
        status TEXT DEFAULT 'pending', -- pending, verified, failed
        gateway TEXT DEFAULT 'zarinpal_sandbox',
        ref_id TEXT,
        description TEXT,
        idempotency_key TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verified_at TIMESTAMP
    );
    """)

    # 10. Application Experiments (A/B testing time slots)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS application_experiments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        job_id TEXT NOT NULL,
        time_slot TEXT NOT NULL, -- 'golden_08_10', 'midday_11_13', 'afternoon_14_16'
        sent_timestamp TIMESTAMP,
        outcome TEXT DEFAULT 'pending', -- pending, viewed, responded, interview, ghosted
        outcome_updated_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # --- Composite Indexes (db-schema-design) ---
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON jobs(job_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created_status ON jobs(created_at, status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_jobs_composite ON user_jobs(user_id, job_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_jobs_user_status ON user_jobs(user_id, status, created_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user_action ON audit_logs(user_id, action, created_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id, status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiments_slot ON application_experiments(time_slot, outcome);")

    # Safe column additions if migrating from older sqlite schema
    for tbl in ["jobs", "user_jobs"]:
        try:
            cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN is_deleted INTEGER DEFAULT 0")
        except Exception:
            pass
        try:
            cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN deleted_at TIMESTAMP")
        except Exception:
            pass
    for col, col_type in [("rubric_breakdown", "TEXT DEFAULT '{}'"), ("hiring_recommendation", "TEXT"), ("candidate_tier", "TEXT"), ("candidate_consent", "INTEGER DEFAULT 1")]:
        try:
            cursor.execute(f"ALTER TABLE interviews ADD COLUMN {col} {col_type}")
        except Exception:
            pass
    try:
        cursor.execute("ALTER TABLE user_jobs ADD COLUMN requires_confirmation INTEGER DEFAULT 1")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE user_jobs ADD COLUMN user_confirmed INTEGER DEFAULT 0")
    except Exception:
        pass

    # Insert default profile if not exists
    cursor.execute("SELECT COUNT(*) FROM profiles")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO profiles (full_name, target_title, target_city, golden_hour_enabled, match_threshold, daily_cap)
        VALUES ('علی رجوند (Ali Ajvand)', 'Data Scientist & BI Professional', 'تهران', 1, 70, 15)
        """)

    # Insert default accounts for Jobinja and Jobvision if not exists
    cursor.execute("SELECT COUNT(*) FROM accounts")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO accounts (platform, username_or_email, status)
        VALUES 
        ('jobinja', '09195253462', 'connected'),
        ('jobvision', '09195253462', 'connected')
        """)

    conn.commit()
    conn.close()

def log_audit(user_id: Optional[int], action: str, entity_type: str, entity_id: Optional[str] = None, changes: Optional[dict] = None, ip_address: Optional[str] = None):
    """Logs security and data modification events for OWASP audit compliance."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, changes_json, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, action, entity_type, str(entity_id) if entity_id else "", json.dumps(changes or {}, ensure_ascii=False), ip_address or "127.0.0.1"))
        conn.commit()
        conn.close()
    except Exception:
        pass

def soft_delete_job(job_id: str, user_id: Optional[int] = None) -> bool:
    """Soft deletes a job by setting is_deleted=1 and recording timestamp."""
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("UPDATE jobs SET is_deleted = 1, deleted_at = ? WHERE job_id = ?", (now, job_id))
    if user_id:
        cur.execute("UPDATE user_jobs SET is_deleted = 1, deleted_at = ? WHERE job_id = ? AND user_id = ?", (now, job_id, user_id))
    conn.commit()
    conn.close()
    log_audit(user_id, "soft_delete", "job", job_id)
    return True

def get_user_job_stats(user_id: int) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE is_deleted = 0")
    total_jobs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM user_jobs WHERE user_id = ? AND status = 'applied' AND is_deleted = 0", (user_id,))
    total_applied = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM user_jobs WHERE user_id = ? AND status = 'queued_golden_hour' AND is_deleted = 0", (user_id,))
    golden_hour_queue = cursor.fetchone()[0]
    conn.close()
    return {
        "total_jobs": total_jobs,
        "total_applied": total_applied,
        "golden_hour_queue": golden_hour_queue
    }

def get_user_jobs_list(user_id: int, limit: int = 10, include_deleted: bool = False) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    del_clause = "" if include_deleted else "AND (j.is_deleted = 0 OR j.is_deleted IS NULL) AND (uj.is_deleted = 0 OR uj.is_deleted IS NULL)"
    cursor.execute(f"""
    SELECT 
        j.id, j.job_id, j.platform, j.title, j.company, j.location, j.salary_range, j.url, j.description, j.skills_required,
        COALESCE(uj.match_score, 0) as match_score,
        COALESCE(uj.match_reasons, '[]') as match_reasons,
        COALESCE(uj.missing_skills, '[]') as missing_skills,
        COALESCE(uj.status, 'discovered') as status,
        COALESCE(uj.requires_confirmation, 1) as requires_confirmation,
        COALESCE(uj.user_confirmed, 0) as user_confirmed,
        uj.tracking_code,
        uj.applied_at
    FROM jobs j
    LEFT JOIN user_jobs uj ON j.job_id = uj.job_id AND uj.user_id = ?
    WHERE 1=1 {del_clause}
    ORDER BY uj.match_score DESC, j.id DESC
    LIMIT ?
    """, (user_id, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def upsert_user_job(user_id: int, job_id: str, match_score: int, match_reasons: list, missing_skills: list, status: str, requires_confirmation: int = 1):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO user_jobs (user_id, job_id, match_score, match_reasons, missing_skills, status, requires_confirmation, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id, job_id) DO UPDATE SET
        match_score = excluded.match_score,
        match_reasons = excluded.match_reasons,
        missing_skills = excluded.missing_skills,
        status = CASE WHEN user_jobs.status = 'applied' THEN 'applied' ELSE excluded.status END,
        requires_confirmation = excluded.requires_confirmation,
        updated_at = excluded.updated_at
    """, (
        user_id, job_id, match_score,
        json.dumps(match_reasons, ensure_ascii=False),
        json.dumps(missing_skills, ensure_ascii=False),
        status, requires_confirmation, now
    ))
    conn.commit()
    conn.close()

def apply_user_job(user_id: int, job_id: str, tracking_code: str):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO user_jobs (user_id, job_id, status, tracking_code, applied_at, user_confirmed, updated_at)
    VALUES (?, ?, 'applied', ?, ?, 1, ?)
    ON CONFLICT(user_id, job_id) DO UPDATE SET
        status = 'applied',
        tracking_code = excluded.tracking_code,
        applied_at = excluded.applied_at,
        user_confirmed = 1,
        updated_at = excluded.updated_at
    """, (user_id, job_id, tracking_code, now, now))
    conn.commit()
    conn.close()
    log_audit(user_id, "apply_job", "job", job_id, {"tracking_code": tracking_code})

if __name__ == "__main__":
    init_db()
    print("Core database schema initialized successfully with audit logs and composite indexes.")
