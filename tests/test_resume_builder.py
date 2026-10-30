"""
Comprehensive Test Suite for Resume Builder, AI ATS Enhancer, Tailor, and Batch Auto-Apply.
Built with skills: qa-reviewer + prompt-engineering + db-schema-design
"""

import pytest
import io
from fastapi.testclient import TestClient
from backend.app import app
from core.db import get_connection, init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_resume_save_endpoint():
    payload = {
        "user_id": 1,
        "full_name": "علی رجوند (Ali Ajvand)",
        "target_title": "Lead Data Scientist & BI Architect",
        "target_city": "تهران",
        "phone": "09195253462",
        "email": "aliajvand@gmail.com",
        "summary": "متخصص ارشد داده با تسلط بر پایتون و هوش تجاری",
        "experience": "• طراحی پایپ‌لاین داده با ۳۵٪ کاهش تاخیر\n• پیاده‌سازی سیستم RAG با دقت ۹۲٪",
        "skills": ["پایتون", "SQL", "Power BI", "RAG", "FAISS"],
        "education": "مهندسی کامپیوتر دانشگاه علوم و تحقیقات",
        "projects": "رتبه ۲ هکاتون پُل ۴"
    }

    res = client.post("/api/resume/save", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True

    # Verify directly from database
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT target_title, target_city, phone, summary, experience FROM profiles WHERE id = 1")
    row = cur.fetchone()
    conn.close()

    assert row["target_title"] == "Lead Data Scientist & BI Architect"
    assert row["target_city"] == "تهران"
    assert row["phone"] == "09195253462"
    assert "پایتون" in row["summary"]
    assert "RAG" in row["experience"]

def test_resume_ai_enhance_endpoint():
    payload = {
        "user_id": 1,
        "target_title": "Senior Data Analyst",
        "summary": "من تحلیل داده انجام می‌دهم با پایتون و اکسل.",
        "experience": "داشبورد درست می‌کردم و کوئری می‌نوشتم.",
        "skills": ["پایتون", "SQL"]
    }

    res = client.post("/api/resume/ai-enhance", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["ats_score"] >= 95
    assert len(data["enhanced_summary"]) > 50
    assert "enhanced_experience" in data
    assert len(data["improvements_applied"]) >= 2

def test_resume_tailor_endpoint():
    # Pick first available job_id
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT job_id FROM jobs LIMIT 1")
    job_row = cur.fetchone()
    conn.close()

    assert job_row is not None
    job_id = job_row["job_id"]

    res = client.post("/api/resume/tailor", json={"user_id": 1, "job_id": job_id})
    assert res.status_code == 200
    data = res.json()
    assert "tailored_summary" in data or "tailored_cover_note" in data
    if "tailored_cover_note" in data:
        assert len(data["tailored_cover_note"]) > 30

def test_resume_upload_endpoint_with_bytes():
    from pathlib import Path
    real_pdf = Path(r"D:\startup\Ali_Ajvand_Resume (12) (1).pdf")
    if real_pdf.exists():
        content = real_pdf.read_bytes()
        filename = "Ali_Ajvand_Resume.pdf"
    else:
        content = "علی رجوند - متخصص علم داده و هوش تجاری مسلط به پایتون، SQL و یادگیری ماشین".encode("utf-8")
        filename = "Ali_Ajvand_Resume.txt"

    files = {"file": (filename, io.BytesIO(content), "application/pdf" if filename.endswith(".pdf") else "text/plain")}

    res = client.post("/api/resume/upload?user_id=1", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "ats_score" in data
    assert "sections" in data
    assert isinstance(data["sections"], dict)

def test_batch_apply_all_endpoint():
    res = client.post("/api/apply/batch-all", json={"user_id": 1})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] in [True, False] # True if applied, False if cap exceeded
    assert "total_applied" in data
    assert "applied_jobs" in data
