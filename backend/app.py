import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from core.config import settings
from core.db import init_db, get_connection, get_user_job_stats, get_user_jobs_list
from core.doc_parser import doc_parser
from agents.resume_analyzer import resume_analyzer_agent
from agents.market_salary_agent import market_salary_agent
from agents.job_hunter import job_hunter_agent
from agents.matcher_agent import job_matcher_agent
from agents.interview_agent import interview_simulator_agent
from agents.auto_applier import auto_applier_agent
from automation.platform_auth import platform_auth_manager, add_log

app = FastAPI(title="Job Career Co-Pilot API", version="2.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
init_db()

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "web_dashboard"

@app.get("/api/status")
def get_system_status(user_id: int = 1):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM profiles WHERE id = ?", (user_id,))
    profile = dict(cursor.fetchone() or {})
    
    cursor.execute("SELECT COUNT(*) FROM interviews")
    total_interviews = cursor.fetchone()[0]
    conn.close()

    stats = get_user_job_stats(user_id)
    
    return {
        "status": "online",
        "user_id": user_id,
        "ats_score": profile.get("ats_score", 0),
        "total_jobs": stats["total_jobs"],
        "total_applied": stats["total_applied"],
        "golden_hour_queue": stats["golden_hour_queue"],
        "total_interviews": total_interviews,
        "golden_hour_enabled": bool(profile.get("golden_hour_enabled", 1)),
        "match_threshold": profile.get("match_threshold", 70),
        "daily_cap": profile.get("daily_cap", 15)
    }

@app.get("/api/accounts")
def get_accounts():
    return platform_auth_manager.get_accounts()

@app.post("/api/accounts/update")
def update_account(payload: dict = Body(...)):
    platform = payload.get("platform")
    username = payload.get("username", "")
    password = payload.get("password", "")
    phone = payload.get("phone", "")
    if not platform:
        raise HTTPException(status_code=400, detail="پلتفرم الزامی است.")
    res = platform_auth_manager.update_account(platform, username, password, phone)
    return res

@app.get("/api/logs")
def get_logs(limit: int = 30):
    return platform_auth_manager.get_recent_logs(limit)

@app.get("/api/profile")
def get_profile(user_id: int = 1):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {}
    res = dict(row)
    for f in ["parsed_skills", "improvement_tips", "missing_trend_skills"]:
        if isinstance(res.get(f), str):
            try:
                res[f] = json.loads(res[f])
            except Exception:
                res[f] = []
    return res

@app.post("/api/profile/update")
def update_profile(user_id: int = 1, data: dict = Body(...)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE profiles
    SET target_title = COALESCE(?, target_title),
        target_city = COALESCE(?, target_city),
        golden_hour_enabled = COALESCE(?, golden_hour_enabled),
        match_threshold = COALESCE(?, match_threshold),
        daily_cap = COALESCE(?, daily_cap),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (
        data.get("target_title"),
        data.get("target_city"),
        data.get("golden_hour_enabled"),
        data.get("match_threshold"),
        data.get("daily_cap"),
        user_id
    ))
    conn.commit()
    conn.close()
    add_log("Settings", f"تنظیمات اتوماسیون کاربر {user_id} با موفقیت به‌روزرسانی شد.", "info")
    return {"success": True, "message": "تنظیمات با موفقیت ذخیره شد."}

@app.post("/api/resume/upload")
async def upload_resume_file(user_id: int = 1, file: UploadFile = File(...)):
    allowed_exts = [".pdf", ".docx", ".doc", ".txt", ".md"]
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="لطفاً فایل با فرمت PDF یا DOCX بارگذاری کنید.")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="فایل انتخاب شده خالی است.")

    extracted_text = doc_parser.parse_bytes(content, file.filename)
    if not extracted_text or len(extracted_text.strip()) < 15:
        raise HTTPException(status_code=400, detail="متن قابل خواندنی در فایل رزومه یافت نشد.")

    add_log("ResumeParser", f"فایل رزومه '{file.filename}' خوانده شد. آغاز تحلیل با ایجنت برای کاربر {user_id}...", "info")
    analysis_res = resume_analyzer_agent.analyze(extracted_text, user_id=user_id)
    analysis_res["extracted_length"] = len(extracted_text)
    analysis_res["filename"] = file.filename
    analysis_res["raw_extracted_text"] = extracted_text[:1200]

    # Automatically calculate personalized job matches for this user
    try:
        job_matcher_agent.match_all_jobs_for_user(user_id=user_id)
    except Exception as e:
        print("Auto match error:", e)

    add_log("ResumeAnalyzer", f"تحلیل رزومه کامل شد. نمره ATS: {analysis_res.get('ats_score')}", "success")
    return analysis_res

@app.post("/api/resume/analyze")
def analyze_resume(payload: dict = Body(...)):
    text = payload.get("resume_text", "")
    user_id = payload.get("user_id", 1)
    res = resume_analyzer_agent.analyze(text, user_id=user_id)
    return res

@app.get("/api/market/benchmarks")
def get_benchmarks(role: str = "data_analyst", level: str = "mid"):
    data = market_salary_agent.get_benchmark(role, level)
    roles = market_salary_agent.get_all_roles()
    return {"benchmark": data, "roles": roles}

@app.get("/api/jobs")
def get_jobs(user_id: int = 1):
    jobs = get_user_jobs_list(user_id=user_id, limit=30)
    if not jobs:
        jobs = job_hunter_agent.get_all_jobs()
    return jobs

@app.post("/api/jobs/hunt")
def hunt_jobs(payload: dict = Body(default={})):
    query = payload.get("query", "دیتا آنالیست")
    city = payload.get("city", "تهران")
    add_log("JobHunter", f"در حال رصد آگهی‌های تازه برای '{query}' در {city}...", "info")
    discovered = job_hunter_agent.hunt_jobs(query, city)
    add_log("JobHunter", f"تعداد {len(discovered)} آگهی کشف و در دیتابیس ثبت شد.", "success")
    return {"count": len(discovered), "jobs": discovered}

@app.post("/api/jobs/match")
def match_job(payload: dict = Body(...)):
    job_id = payload.get("job_id")
    user_id = payload.get("user_id", 1)
    if not job_id:
        raise HTTPException(status_code=400, detail="Job ID required")
    res = job_matcher_agent.evaluate_job(job_id, user_id=user_id)
    add_log("JobMatcher", f"انطباق آگهی {job_id} بررسی شد: {res.get('match_score')}% ({res.get('new_status')})", "info")
    return res

@app.post("/api/jobs/apply")
def apply_job(payload: dict = Body(...)):
    job_id = payload.get("job_id")
    user_id = payload.get("user_id", 1)
    if not job_id:
        raise HTTPException(status_code=400, detail="Job ID required")
    res = platform_auth_manager.execute_live_apply(job_id, user_id=user_id)
    return res

@app.post("/api/interview/question")
def get_interview_question(payload: dict = Body(...)):
    title = payload.get("job_title", "تحلیل‌گر داده")
    company = payload.get("company", "گروه اسنپ")
    res = interview_simulator_agent.get_question_for_job(title, company)
    add_log("InterviewRoom", f"سوال جدید مصاحبه برای شرکت {company} طراحی شد.", "info")
    return res

@app.post("/api/interview/evaluate")
def evaluate_interview(payload: dict = Body(...)):
    title = payload.get("job_title", "تحلیل‌گر داده")
    company = payload.get("company", "گروه اسنپ")
    question = payload.get("question", "")
    answer = payload.get("user_answer", "")
    res = interview_simulator_agent.evaluate_answer(title, company, question, answer)
    add_log("InterviewRoom", f"پاسخ کاربر ارزیابی شد. نمره کسب شده: {res.get('score')}/100", "success")
    return res

@app.get("/api/banners")
def get_banners():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM banners WHERE is_active = 1")
    banners = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return banners

# Mount frontend
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Job Career Co-Pilot API is running. Open /docs for Swagger UI."}
