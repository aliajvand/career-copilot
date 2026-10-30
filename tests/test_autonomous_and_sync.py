import pytest
from core.db import init_db, get_connection
from agents.autonomous_agent import autonomous_agent
from automation.platform_auth import sync_resume_to_platforms
from agents.interview_agent import interview_simulator_agent
from agents.market_salary_agent import market_salary_agent

def setup_module():
    init_db()

def test_autonomous_scan_30_days():
    res = autonomous_agent.scan_and_auto_apply_past_30_days(user_id=1, days_back=30)
    assert res["success"] is True
    assert "scan_metrics" in res
    assert res["scan_metrics"]["total_scanned"] >= 5
    assert "applied_count" in res["scan_metrics"]

def test_autonomous_toggle():
    res1 = autonomous_agent.set_24h_monitoring(user_id=1, enable=True)
    assert res1["success"] is True
    assert res1["autonomous_24h_active"] is True

    res2 = autonomous_agent.set_24h_monitoring(user_id=1, enable=False)
    assert res2["success"] is True
    assert res2["autonomous_24h_active"] is False

    # Re-enable
    autonomous_agent.set_24h_monitoring(user_id=1, enable=True)

def test_sync_resume_to_platforms():
    res = sync_resume_to_platforms(user_id=1)
    assert res["success"] is True
    assert "platforms" in res
    assert "jobinja" in res["platforms"]
    assert "jobvision" in res["platforms"]
    assert res["platforms"]["jobinja"]["status"] == "SYNCED_ONLINE_CV_AND_PDF"
    assert res["platforms"]["jobvision"]["status"] == "SYNCED_ONLINE_CV_AND_PDF"

def test_interview_intro_and_drill_modes():
    # 1. Test company intro & Dr. Kian Radmanesh persona
    intro = interview_simulator_agent.get_interview_intro("Data Scientist", "گروه اسنپ (Snapp Group)", "علی رجوند")
    assert "کیان رادمنش" in intro["interviewer_name"]
    assert "company_intro" in intro
    assert "speech_text" in intro
    assert "علی" in intro["speech_text"]

    # 2. Test drill mode question Level 1
    q1 = interview_simulator_agent.get_question_for_job(
        "تحلیل‌گر داده", "دیجی‌کالا", mode="drill", topic="python", stage="level1_easy"
    )
    assert "question" in q1
    assert len(q1["question"]) > 10

    # 3. Test drill mode question Level 3
    q3 = interview_simulator_agent.get_question_for_job(
        "تحلیل‌گر داده", "دیجی‌کالا", mode="drill", topic="rag", stage="level3_architecture"
    )
    assert "question" in q3
    assert len(q3["question"]) > 10

def test_market_salary_city_benchmarks():
    # Tehran (1.0x)
    tehran = market_salary_agent.get_benchmark("data_scientist", "senior", city="تهران")
    assert tehran["median_salary"] == 95.0
    assert tehran["min_salary"] == 75.0

    # Isfahan (0.85x)
    isfahan = market_salary_agent.get_benchmark("data_scientist", "senior", city="اصفهان")
    assert isfahan["median_salary"] == 80.8
    assert isfahan["min_salary"] == 63.8
    assert "جاب‌ویژن" in isfahan["data_source"]
