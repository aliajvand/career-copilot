import unittest
from agents.interview_agent import interview_simulator_agent

class TestB2BInterviewSimulator(unittest.TestCase):

    def test_inter_rater_consistency_10_samples(self):
        samples = [
            # Strong
            {"tier": "strong", "text": "من ابتدا با بررسی دقیق لاگ‌های Slow Query و اجرای EXPLAIN ANALYZE پلن اجرایی کوئری را استخراج می‌کنم. سپس با ایجاد کامپوزیت ایندکس روی فیلدهای فیلتر و مانیتورینگ بلادرنگ در Grafana تاخیر را به زیر ۱۰۰ میلی‌ثانیه می‌رسانم."},
            {"tier": "strong", "text": "برای مقیاس‌پذیری کمپین، از مکانیزم Read Replica و کشینگ Redis با استراتژی Cache-Aside استفاده می‌کنم تا بار از دیتابیس اصلی برداشته شود و فرآیندهای سنگین به صورت صف ناهمگام در Celery اجرا شوند."},
            {"tier": "strong", "text": "در تحلیل افت تکمیل سفر، همبستگی شاخص عرضه رانندگان را با نرخ لغو در هر منطقه بررسی کرده و فانل ثبت تا قبول درخواست را می‌سنجم تا ریشه افت مشخص شود."},
            {"tier": "strong", "text": "در معماری ایجنتی، حافظه کوتاه‌مدت و بلندمدت را با پایگاه برداری FAISS جدا کرده و با گاردریل اعتبارسنجی خروجی، خطا را به حداقل می‌رسانم."},
            {"tier": "strong", "text": "برای مدیریت داده‌های حساس، کوکی‌ها و توکن‌ها را با الگوریتم متقارن Fernet بر پایه کلید مشتق‌شده PBKDF2 رمزگذاری می‌کنم تا نشت اطلاعات غیرممکن شود."},
            
            # Mid
            {"tier": "mid", "text": "من با تیم فنی صحبت می‌کنم و بعد از آن کدها را بررسی می‌کنم و سعی می‌کنم کوئری‌ها را بازنویسی کنم تا سریع‌تر اجرا شوند."},
            {"tier": "mid", "text": "از اکسل و گزارش‌های روزانه استفاده می‌کنم تا ببینم کدام منطقه سفر کمتری داشته و به رانندگان پیامک تخفیف می‌فرستیم."},
            {"tier": "mid", "text": "پایتون و کتابخانه پانداس را برای تمیزکاری داده به کار می‌گیرم و نتایج را در قالب فایل اکسل به مدیر ارائه می‌دهم."},

            # Weak
            {"tier": "weak", "text": "مشکل را حل می‌کنم چون تخصص دارم."},
            {"tier": "weak", "text": "کوئری را دوباره اجرا می‌کنم."}
        ]

        scores = []
        for s in samples:
            res = interview_simulator_agent.evaluate_answer(
                job_title="Data Specialist",
                company="شرکت آزمایشی",
                question="چالش بهینه‌سازی سیستم",
                user_answer=s["text"],
                candidate_consent=True
            )
            scores.append((s["tier"], res["score"], res.get("hiring_recommendation")))

        # Consistency assertions
        strong_avg = sum(sc[1] for sc in scores if sc[0] == "strong") / 5
        mid_avg = sum(sc[1] for sc in scores if sc[0] == "mid") / 3
        weak_avg = sum(sc[1] for sc in scores if sc[0] == "weak") / 2

        self.assertGreater(strong_avg, mid_avg, "Strong answers must score higher than mid")
        self.assertGreater(mid_avg, weak_avg, "Mid answers must score higher than weak")

    def test_b2b_report_generation(self):
        eval_res = interview_simulator_agent.evaluate_answer(
            job_title="Senior Data Analyst",
            company="دیجی‌کالا",
            question="بهینه‌سازی سیستم‌های بلادرنگ",
            user_answer="ایجاد سیستم کشینگ دو سطحی و صف پیام Kafka جهت حفظ پایداری سیستم در ترافیک بالا.",
            candidate_consent=True
        )
        report = interview_simulator_agent.generate_b2b_report(eval_res["interview_id"])
        self.assertIn("report_title", report)
        self.assertIn("hiring_recommendation", report)
        self.assertIn("rubric_breakdown", report)
        self.assertTrue(report["compliance"]["consent_verified"])

if __name__ == "__main__":
    unittest.main()
