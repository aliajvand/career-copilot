import io
import sys
import json
import pytest
from pathlib import Path

# Configure utf-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

from core.db import init_db, get_connection
from core.doc_parser import doc_parser
from agents.resume_analyzer import resume_analyzer_agent
from agents.market_salary_agent import market_salary_agent
from agents.job_hunter import job_hunter_agent
from agents.matcher_agent import job_matcher_agent
from agents.auto_applier import auto_applier_agent
from agents.interview_agent import interview_simulator_agent

def test_document_parser_pdf_and_docx():
    print("\n--- 1. Testing Document Parser (PDF & DOCX) ---")
    
    # 1. Test DOCX
    import docx
    d = docx.Document()
    d.add_heading("رزومه تخصصی تحلیل داده", 0)
    d.add_paragraph("مسلط به SQL, Python, Power BI و اتوماسیون با Vibe Coding")
    buf = io.BytesIO()
    d.save(buf)
    docx_text = doc_parser.parse_bytes(buf.getvalue(), "cv.docx")
    assert "Vibe Coding" in docx_text, "DOCX parser failed"
    print("✓ DOCX parser passed successfully.")

    # 2. Test PDF
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Alireza - Data Analyst - AI Agents - Vibe Coding")
    pdf_bytes = doc.tobytes()
    doc.close()
    pdf_text = doc_parser.parse_bytes(pdf_bytes, "cv.pdf")
    assert "AI Agents" in pdf_text, "PDF parser failed"
    print("✓ PDF parser passed successfully.")

def test_resume_analyzer():
    print("\n--- 2. Testing Resume Analyzer Agent ---")
    resume_text = """
    کارشناس تحلیل داده با ۳ سال سابقه کار در تیم‌های چابک.
    مهارت‌ها: Python, SQL پیشرفته, Power BI, مدل‌سازی داده، ساخت پایپ‌لاین‌های ETL.
    تحصیلات: کارشناسی ارشد مهندسی صنایع دانشگاه تهران.
    """
    res = resume_analyzer_agent.analyze(resume_text)
    assert res["ats_score"] > 60, "ATS score too low"
    assert "detected_skills" in res, "Missing detected skills"
    assert len(res["missing_trend_skills"]) > 0, "Missing trend skills detection failed"
    print(f"✓ ATS Score: {res['ats_score']}")
    print(f"✓ Detected Skills: {res['detected_skills']}")
    print(f"✓ Missing Trends: {[m['skill'] for m in res['missing_trend_skills']]}")

def test_market_salary_agent():
    print("\n--- 3. Testing Market Salary Agent ---")
    b = market_salary_agent.get_benchmark("data_analyst", "mid")
    assert b["median_salary"] == 45, "Median salary mismatch"
    assert "45 الی 58" in b["recommended_bid"]
    print(f"✓ Salary Benchmark for {b['role_fa']}: {b['min_salary']} to {b['max_salary']} M Tomans")

def test_job_hunter_and_duplication():
    print("\n--- 4. Testing Job Hunter & Duplicate Protection ---")
    jobs = job_hunter_agent.hunt_jobs("دیتا آنالیست", "تهران")
    assert len(jobs) >= 5, "Jobs hunt returned too few listings"
    all_stored = job_hunter_agent.get_all_jobs()
    job_ids = [j["job_id"] for j in all_stored]
    # Check uniqueness
    assert len(job_ids) == len(set(job_ids)), "Duplicate job_ids found in database!"
    print(f"✓ Discovered {len(jobs)} unique jobs without duplicates.")

def test_matcher_agent():
    print("\n--- 5. Testing Job Matcher Agent ---")
    jobs = job_hunter_agent.get_all_jobs()
    target_job = jobs[0]
    match_res = job_matcher_agent.evaluate_job(target_job["job_id"])
    assert "match_score" in match_res
    print(f"✓ Match Score for '{target_job['title']}': {match_res['match_score']}%")
    print(f"✓ Resulting Status: {match_res['new_status']}")

def test_auto_applier_and_duplicate_lock():
    print("\n--- 6. Testing Auto Applier & Anti-Spam Lock ---")
    jobs = job_hunter_agent.get_all_jobs()
    # Find an unapplied job
    target = None
    for j in jobs:
        if j["status"] != "applied":
            target = j
            break
            
    if target:
        # First apply should succeed
        res1 = auto_applier_agent.apply_to_job(target["job_id"], bypass_cap=True)
        assert res1["success"] is True, f"Application failed: {res1}"
        print(f"✓ Successfully applied to: {target['company']}")

        # Second apply to same job MUST fail
        res2 = auto_applier_agent.apply_to_job(target["job_id"], bypass_cap=True)
        assert res2["success"] is False, "Duplicate application was not prevented!"
        print(f"✓ Re-application successfully blocked with error: {res2['error']}")

def test_interview_simulator():
    print("\n--- 7. Testing AI Interview Simulator Agent ---")
    q_data = interview_simulator_agent.get_question_for_job("تحلیل‌گر داده", "اسنپ")
    assert "question" in q_data
    print(f"✓ Generated Question: {q_data['question'][:80]}...")

    eval_data = interview_simulator_agent.evaluate_answer(
        "تحلیل‌گر داده", 
        "اسنپ", 
        q_data["question"], 
        "من ابتدا پلن اجرای کوئری را بررسی کرده و سپس ایندکس‌های کامپوزیت روی جدول سفارشات می‌سازم."
    )
    assert eval_data["score"] >= 60
    assert "feedback" in eval_data
    print(f"✓ Evaluation Score: {eval_data['score']}/100")
    print(f"✓ AI Feedback: {eval_data['feedback'][:80]}...")

if __name__ == "__main__":
    init_db()
    test_document_parser_pdf_and_docx()
    test_resume_analyzer()
    test_market_salary_agent()
    test_job_hunter_and_duplication()
    test_matcher_agent()
    test_auto_applier_and_duplicate_lock()
    test_interview_simulator()
    print("\n" + "=" * 50)
    print("🎉 ALL 7 TEST SUITES PASSED FLAWLESSLY!")
    print("=" * 50)
