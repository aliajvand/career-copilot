import json
import re
from core.db import get_connection
from agents.gemini_client import gemini_client

class InterviewSimulatorAgent:
    """
    Agent responsible for:
    - Generating realistic, high-pressure yet confidence-building interview questions
      tailored to the specific company (e.g. Snapp, Digikala) and job role
    - Evaluating the user's answer
    - Providing constructive scoring (0-100), key improvement tips, and a sample ideal answer
    """
    
    DEFAULT_QUESTIONS = {
        "snapp": [
            {
                "question": "فرض کنید زمان پاسخگویی به یک کوئری تحلیلی در پایگاه داده سفارشات اسنپ از ۴ ثانیه به ۲۵ ثانیه افزایش پیدا کرده و مدیر محصول به شدت نگران است. قدم به قدم چگونه مشکل را ریشه‌یابی و حل می‌کنید؟",
                "type": "Technical / Problem Solving",
                "focus": "SQL Optimization, Indexing, Execution Plan"
            },
            {
                "question": "در صورتی که نرخ تکمیل سفرهای یک منطقه در تهران به طور ناگهانی ۱۵٪ افت کند، چه شاخص‌هایی را بررسی می‌کنید تا بفهمید مشکل از کمبود راننده است یا نقص فنی اپلیکیشن؟",
                "type": "Business Analytics",
                "focus": "Funnel Analysis, Supply-Demand Metrics"
            }
        ],
        "digikala": [
            {
                "question": "در حین کمپین بلک فرایدی دیجی‌کالا، چگونه اطمینان حاصل می‌کنید که داده‌های کمپین بلادرنگ (Real-time) بدون ایجاد بار اضافی روی سرورهای تراکنش اصلی پردازش می‌شوند؟",
                "type": "Data Pipeline",
                "focus": "ETL, Caching, Read Replicas"
            }
        ],
        "default": [
            {
                "question": "بزرگ‌ترین چالشی که در تمیزسازی یا مدل‌سازی داده‌ها در پروژه‌های قبلی‌تان داشتید چه بود و چگونه با کمک ابزارهای مدرن (پایتون/هوش مصنوعی) آن را مدیریت کردید؟",
                "type": "Behavioral & Technical",
                "focus": "STAR Method (Situation, Task, Action, Result)"
            },
            {
                "question": "تفاوت بین استفاده سنتی از داشبوردهای آماده با توسعه پایپ‌لاین‌های خودکار مبتنی بر ایجنت‌های هوش مصنوعی (Agentic Workflows) را چطور ارزیابی می‌کنید؟",
                "type": "Modern Tech Trends",
                "focus": "AI Automation, Business Impact"
            }
        ]
    }

    def get_question_for_job(self, job_title: str, company: str) -> dict:
        comp_key = "default"
        company_lower = company.lower()
        if "اسنپ" in company_lower or "snapp" in company_lower:
            comp_key = "snapp"
        elif "دیجی" in company_lower or "digikala" in company_lower:
            comp_key = "digikala"

        prompt = f"""
        تو مدیر ارشد مصاحبه‌کننده در شرکت {company} برای موقعیت شغلی "{job_title}" در تهران هستی.
        یک سوال فنی و تحلیلی بسیار واقعی، چالش‌برانگیز و جذاب برای این مصاحبه طراحی کن.
        فرمت خروجی به صورت JSON:
        {{
            "question": "متن سوال به زبان فارسی صریح و حرفه‌ای",
            "type": "دسته‌بندی سوال (تخصصی / حل مسئله / رفتاری)",
            "context": "سناریوی مرتبط با چالش‌های شرکت {company}",
            "hint": "راهنمایی کلیدی برای پاسخ‌دهی استاندارد"
        }}
        """

        raw = gemini_client.generate_content(prompt)
        res = None
        if raw:
            try:
                clean_json = re.sub(r'```json\s*', '', raw)
                clean_json = re.sub(r'```\s*', '', clean_json).strip()
                res = json.loads(clean_json)
            except Exception:
                res = None

        if not res:
            q_list = self.DEFAULT_QUESTIONS.get(comp_key, self.DEFAULT_QUESTIONS["default"])
            item = q_list[0]
            res = {
                "question": item["question"],
                "type": item["type"],
                "context": f"سناریوی واقعی در تیم فنی {company}",
                "hint": f"روی مفاهیم {item['focus']} تمرکز کنید و با ساختار STAR پاسخ دهید."
            }

        return res

    def evaluate_answer(self, job_title: str, company: str, question: str, user_answer: str) -> dict:
        if not user_answer or len(user_answer.strip()) < 10:
            return {
                "score": 40,
                "feedback": "پاسخ شما بسیار کوتاه بود. در مصاحبه باید فرآیند فکری خود را قدم‌به‌قدم با مثال‌های ملموس شرح دهید.",
                "sample_ideal_answer": "من ابتدا لاگ‌های سرور و Execution Plan کوئری را بررسی می‌کردم تا متوجه Full Table Scan احتمالی بشوم. سپس با اضافه کردن Composite Index مناسب یا پارتیشن‌بندی، سرعت اجرا را به زیر ۱ ثانیه می‌رساندم."
            }

        prompt = f"""
        تو یک ارزیاب خبره مصاحبه‌های استخدامی هستی.
        موقعیت: {job_title} در {company}
        سوال مصاحبه: {question}
        پاسخ داوطلب: {user_answer}

        پاسخ را نمره‌دهی کرده و بازخورد سازنده بده. خروجی فقط به صورت JSON:
        {{
            "score": عدد بین 0 تا 100,
            "strengths": ["نقطه مثبت پاسخ"],
            "feedback": "توضیح تحلیلی نقاط ضعف و آنچه مصاحبه‌کننده انتظار شنیدنش را داشت",
            "sample_ideal_answer": "نمونه یک پاسخ ایده‌آل و برنده به زبان فارسی"
        }}
        """

        raw = gemini_client.generate_content(prompt)
        res = None
        if raw:
            try:
                clean_json = re.sub(r'```json\s*', '', raw)
                clean_json = re.sub(r'```\s*', '', clean_json).strip()
                res = json.loads(clean_json)
            except Exception:
                res = None

        if not res:
            # High-grade fallback
            ans_len = len(user_answer.split())
            score = min(92, max(60, 60 + ans_len * 2))
            res = {
                "score": score,
                "strengths": ["بیان منطقی و اشاره به حل مسئله"],
                "feedback": "رویکرد کلی شما صحیح است. برای مصاحبه‌های شرکت‌های تراز اول، بهتر است از معیارهای عددی و ابزارهای مانیتورینگ دقیق‌تر نام ببرید.",
                "sample_ideal_answer": f"در مصاحبه {company}، بهترین پاسخ این است که ابتدا صورت مسئله را شفاف کرده، فرضیه‌سازی کنید و سپس با معرفی ابزارهای دقیق بهینه‌سازی، نتیجه حاصل‌شده را ارزیابی کنید."
            }

        # Save to DB
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO interviews (job_title, company, question, user_answer, score, feedback, sample_ideal_answer)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            job_title,
            company,
            question,
            user_answer,
            res.get("score", 70),
            res.get("feedback", ""),
            res.get("sample_ideal_answer", "")
        ))
        conn.commit()
        conn.close()

        return res

interview_simulator_agent = InterviewSimulatorAgent()
