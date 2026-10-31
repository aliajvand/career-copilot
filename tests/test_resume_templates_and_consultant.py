import unittest
from fastapi.testclient import TestClient
from core.db import init_db
from agents.resume_consultant_agent import resume_consultant_agent
from agents.resume_templates_agent import resume_templates_agent
from backend.app import app

class TestResumeTemplatesAndConsultant(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_01_consultant_agent_get_question(self):
        q = resume_consultant_agent.get_next_question(user_id=1)
        self.assertIn("question", q)
        self.assertIn("topic", q)
        self.assertIn("current_ats", q)
        self.assertGreater(len(q["question"]), 10)
        print(f"✓ Consultant Question: {q['topic']} -> {q['question'][:60]}...")

    def test_02_consultant_agent_process_answer(self):
        sample_answer = "من زمان اجرای پایپ‌لاین‌های داده را ۳۵٪ کاهش دادم و داشبوردهای تحلیلی را برای مدیران ارشد در Power BI توسعه دادم."
        res = resume_consultant_agent.process_candidate_answer(user_id=1, user_input_text=sample_answer)
        self.assertTrue(res.get("success"))
        self.assertIn("added_bullet", res)
        self.assertIn("new_ats", res)
        self.assertGreaterEqual(res["new_ats"], 90)
        print(f"✓ Consultant Processed Answer -> New ATS: {res['new_ats']} | Bullet: {res['added_bullet']}")

    def test_03_templates_list_and_rendering(self):
        templates = resume_templates_agent.get_templates_list()
        self.assertEqual(len(templates), 3)
        ids = [t["id"] for t in templates]
        self.assertIn("harvard_ats", ids)
        self.assertIn("modern_tech", ids)
        self.assertIn("executive_bi", ids)

        for t_id in ids:
            html = resume_templates_agent.render_template_html(user_id=1, template_id=t_id)
            self.assertIn("resume-sheet", html)
            self.assertIn("Ali Ajvand", html)
            self.assertIn("Power BI", html)
            print(f"✓ Template '{t_id}' successfully rendered ({len(html)} chars).")

    def test_04_before_after_comparison(self):
        diff = resume_templates_agent.get_before_after_comparison(user_id=1)
        self.assertEqual(diff.get("score_before"), 62)
        self.assertGreaterEqual(diff.get("score_after", 0), 90)
        self.assertIn("before_metrics", diff)
        self.assertIn("after_metrics", diff)
        self.assertGreaterEqual(len(diff.get("enhancement_highlights", [])), 3)
        print(f"✓ Before vs After: {diff['score_before']}% -> {diff['score_after']}% ({diff['improvement_pct']})")

    def test_05_job_platforms_form_payload(self):
        payload = resume_templates_agent.get_job_platforms_form_payload(user_id=1)
        self.assertIn("jobinja", payload)
        self.assertIn("jobvision", payload)
        self.assertIn("bookmarklet_code", payload)
        self.assertTrue(payload["bookmarklet_code"].startswith("javascript:"))
        self.assertIn("Ali Ajvand", payload["candidate_name"])
        self.assertIn("headline", payload["jobinja"])
        self.assertIn("job_title", payload["jobvision"])
        print("✓ Job Platforms Form Payload & Bookmarklet verified.")

    def test_06_fastapi_endpoints(self):
        # 1. Consultant Question
        r1 = self.client.get("/api/consultant/question?user_id=1")
        self.assertEqual(r1.status_code, 200)
        self.assertIn("question", r1.json())

        # 2. Consultant Answer
        r2 = self.client.post("/api/consultant/answer", json={
            "user_id": 1,
            "answer_text": "طراحی پایپ‌لاین داده با نرخ ۹۹.۹٪ پایداری و ادغام پایتون و داکر"
        })
        self.assertEqual(r2.status_code, 200)
        self.assertTrue(r2.json().get("success"))

        # 3. Templates List
        r3 = self.client.get("/api/templates/list")
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(len(r3.json()), 3)

        # 4. Render Template
        r4 = self.client.get("/api/templates/render?user_id=1&template_id=harvard_ats")
        self.assertEqual(r4.status_code, 200)
        self.assertEqual(r4.json()["template_id"], "harvard_ats")
        self.assertIn("Ali Ajvand", r4.json()["html"])

        # 5. Before After
        r5 = self.client.get("/api/templates/before-after?user_id=1")
        self.assertEqual(r5.status_code, 200)
        self.assertEqual(r5.json().get("score_before"), 62)

        # 6. Platforms Form
        r6 = self.client.get("/api/templates/platforms-form?user_id=1")
        self.assertEqual(r6.status_code, 200)
        self.assertIn("bookmarklet_code", r6.json())
        print("✓ All 6 FastAPI endpoints for templates and consultant tested successfully.")

if __name__ == "__main__":
    unittest.main()
