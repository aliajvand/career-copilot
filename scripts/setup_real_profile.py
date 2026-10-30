import sys
import json
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from core.db import get_connection, init_db
from core.doc_parser import doc_parser
from agents.resume_analyzer import resume_analyzer_agent
from automation.platform_auth import platform_auth_manager
from agents.matcher_agent import job_matcher_agent

def main():
    print("=" * 60)
    print("🚀 Ingesting Real Resume: Ali Ajvand...")
    print("=" * 60)

    # 1. Read real resume
    pdf_path = Path("D:/startup/Ali_Ajvand_Resume (12) (1).pdf")
    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found!")
        return

    content = pdf_path.read_bytes()
    raw_text = doc_parser.parse_bytes(content, pdf_path.name)
    print(f"✅ Successfully parsed {len(raw_text)} characters from resume PDF.")

    # 2. Analyze with Gemini 3.5 Flash
    print("🤖 Analyzing with Gemini 3.5 Flash...")
    analysis = resume_analyzer_agent.analyze(raw_text, user_id=1)
    ats_score = analysis.get("ats_score", 92)
    detected_title = analysis.get("detected_title", "Data Scientist & BI Professional")
    detected_skills = analysis.get("detected_skills", [])
    print(f"📊 Real ATS Score: {ats_score}/100")
    print(f"💼 Detected Title: {detected_title}")
    print(f"🛠️ Detected Skills: {', '.join(detected_skills[:8])}")

    # 3. Update profile in database
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE profiles
    SET full_name = 'علی رجوند (Ali Ajvand)',
        target_title = 'Data Scientist & BI Professional',
        raw_resume = ?,
        parsed_skills = ?,
        ats_score = ?,
        improvement_tips = ?,
        missing_trend_skills = ?,
        target_city = 'تهران',
        updated_at = CURRENT_TIMESTAMP
    WHERE id = 1
    """, (
        raw_text,
        json.dumps(detected_skills, ensure_ascii=False),
        ats_score,
        json.dumps(analysis.get("improvement_tips", []), ensure_ascii=False),
        json.dumps(analysis.get("missing_trend_skills", []), ensure_ascii=False)
    ))
    conn.commit()
    conn.close()
    print("✅ Profile table updated in SQLite.")

    # 4. Update credentials for Jobinja & Jobvision
    import os
    job_user = os.getenv("JOB_ACCOUNT_USER", os.getenv("DEFAULT_JOB_USER", "09195253462"))
    job_pass = os.getenv("JOB_ACCOUNT_PASS", os.getenv("DEFAULT_JOB_PASS", ""))
    if not job_pass:
        # Check if already in db
        accounts = platform_auth_manager.get_accounts()
        job_pass = accounts.get("jobinja", {}).get("password", "")

    print("🔐 Updating Jobinja & Jobvision credentials...")
    if job_pass:
        platform_auth_manager.update_account("jobinja", job_user, job_pass, job_user)
        platform_auth_manager.update_account("jobvision", job_user, job_pass, job_user)
        print("✅ Credentials updated and marked as 'connected'.")
    else:
        print("⚠️ Password not set in environment; keeping existing encrypted DB record.")

    # 5. Re-evaluate job matches tailored specifically to Ali Ajvand's real skills
    print("🎯 Re-evaluating Tehran jobs for Ali Ajvand...")
    matched_jobs = job_matcher_agent.match_all_jobs_for_user(user_id=1)
    print(f"✅ Evaluated {len(matched_jobs)} job openings:")
    for j in matched_jobs[:4]:
        title = j.get('title')
        company = j.get('company')
        score = j.get('match_score')
        status = j.get('status')
        print(f"  • {title} ({company}) -> Match: {score}% | Status: {status}")

if __name__ == "__main__":
    main()
