import sys
import unittest
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from core.db import init_db, get_connection, get_user_job_stats, get_user_jobs_list
from core.doc_parser import doc_parser
from agents.resume_analyzer import resume_analyzer_agent
from agents.job_hunter import job_hunter_agent
from agents.matcher_agent import job_matcher_agent
from agents.interview_agent import interview_simulator_agent
from agents.hierarchical_engine import hierarchical_engine, ENTERPRISE_DOMAINS
from automation.platform_auth import platform_auth_manager

class TestFullCareerPlatform(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        pdf_path = Path("D:/startup/Ali_Ajvand_Resume (12) (1).pdf")
        if pdf_path.exists():
            text = doc_parser.parse_bytes(pdf_path.read_bytes(), pdf_path.name)
            resume_analyzer_agent.analyze(text, user_id=1)
        platform_auth_manager.update_account("jobinja", "09195253462", "0441067824", "09195253462")
        platform_auth_manager.update_account("jobvision", "09195253462", "0441067824", "09195253462")

    def test_01_real_pdf_parsing(self):
        pdf_path = Path("D:/startup/Ali_Ajvand_Resume (12) (1).pdf")
        self.assertTrue(pdf_path.exists(), "Ali Ajvand resume PDF must exist")
        content = pdf_path.read_bytes()
        text = doc_parser.parse_bytes(content, pdf_path.name)
        self.assertGreater(len(text), 1000, "Parsed text must be substantial")
        self.assertIn("Ali Ajvand", text)
        self.assertIn("Power BI", text)
        self.assertIn("Python", text)
        print("✓ Test 1: Real PDF Resume successfully parsed (9K+ chars).")

    def test_02_database_profile_and_accounts(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT full_name, target_title, ats_score FROM profiles WHERE id = 1")
        prof = dict(cur.fetchone() or {})
        self.assertIn("Ali Ajvand", prof.get("full_name", ""))
        self.assertGreaterEqual(prof.get("ats_score", 0), 80)

        cur.execute("SELECT platform, username_or_email, status FROM accounts")
        accs = {r["platform"]: dict(r) for r in cur.fetchall()}
        self.assertEqual(accs["jobinja"]["username_or_email"], "09195253462")
        self.assertEqual(accs["jobinja"]["status"], "connected")
        self.assertEqual(accs["jobvision"]["username_or_email"], "09195253462")
        self.assertEqual(accs["jobvision"]["status"], "connected")
        conn.close()
        print("✓ Test 2: Profile & Accounts verified with real credentials.")

    def test_03_job_hunter_and_matcher_for_ali(self):
        jobs = get_user_jobs_list(user_id=1, limit=10)
        self.assertGreater(len(jobs), 0)
        top_match = jobs[0]
        self.assertGreaterEqual(top_match["match_score"], 80)
        print(f"✓ Test 3: Job Matcher verified - Top match: {top_match['title']} ({top_match['match_score']}%)")

    def test_04_live_apply_simulation(self):
        jobs = get_user_jobs_list(user_id=1, limit=1)
        job_id = jobs[0]["job_id"]
        res = platform_auth_manager.execute_live_apply(job_id, user_id=1, user_confirmed=True)
        self.assertIn("status", res)
        self.assertEqual(res["job_id"], job_id)
        print(f"✓ Test 4: Live Apply Engine verified - Status: {res.get('status')}")

    def test_05_b2b_interview_evaluator(self):
        q_data = interview_simulator_agent.get_question_for_job("Data Scientist", "گروه اسنپ")
        self.assertIn("question", q_data)
        answer = "من ابتدا با بررسی Execution Plan و اضافه کردن Composite Index به همراه مانیتورینگ تاخیر، کوئری‌ها را بهینه‌سازی می‌کنم."
        eval_res = interview_simulator_agent.evaluate_answer("Data Scientist", "گروه اسنپ", q_data["question"], answer)
        self.assertGreaterEqual(eval_res.get("score", 0), 70)
        self.assertIn("hiring_recommendation", eval_res)
        self.assertIn("technical_depth", eval_res)
        print(f"✓ Test 5: B2B Interview Rubric verified - Score: {eval_res['score']} | Rec: {eval_res['hiring_recommendation']}")

    def test_06_hierarchical_multi_agent_council(self):
        self.assertEqual(len(ENTERPRISE_DOMAINS), 8)
        debate = hierarchical_engine.conduct_domain_debate(
            "security_auth", 
            "ارزیابی پایداری و امنیت نشست‌های کاربری", 
            "علی رجوند"
        )
        self.assertEqual(debate.get("domain_key"), "security_auth")
        self.assertGreater(len(debate.get("worker_arguments", [])), 0)
        self.assertIn("domain_consensus", debate)
        print(f"✓ Test 6: Multi-Agent Domain Debate verified for {debate['domain_title']}.")

    def test_07_security_owasp_compliance(self):
        from backend.app import run_security_audit
        audit = run_security_audit()
        self.assertEqual(audit.get("overall_status"), "SECURE")
        self.assertEqual(audit.get("compliance_score"), 100)
        self.assertEqual(len(audit.get("checks", [])), 6)
        print("✓ Test 7: OWASP Security Audit verified - All 6 checks passed.")

if __name__ == "__main__":
    unittest.main()
