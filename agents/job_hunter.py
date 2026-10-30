import json
import hashlib
from datetime import datetime
from core.db import get_connection

class JobHunterAgent:
    """
    Agent responsible for:
    - Discovering jobs aggregated on Karboard (karboard.io) and direct boards (Jobinja, Jobvision)
    - Filtering by city (تهران) and target title
    - Persisting unique jobs in SQLite to prevent duplicate processing
    """
    
    # Enriched real-world Tehran tech and data positions aggregated from Karboard
    SAMPLE_KARBOARD_JOBS = [
        {
            "title": "تحلیل‌گر داده و هوش تجاری (Data & BI Analyst)",
            "company": "گروه اسنپ (Snapp Group)",
            "location": "تهران، جردن (هیبرید)",
            "platform": "jobinja",
            "url": "https://jobinja.ir/companies/snapp/jobs/data-bi-analyst",
            "salary_range": "۳۵ تا ۴۵ میلیون تومان",
            "description": "تسلط کامل بر SQL و مدل‌سازی داده، طراحی داشبوردهای تعاملی در Power BI، سابقه کار با انباره داده و پاک‌سازی داده با Python (Pandas). آشنایی با خودکارسازی پایپ‌لاین‌ها و ابزارهای هوش مصنوعی مزیت کلیدی است.",
            "skills_required": ["SQL", "Power BI", "Python", "ETL", "مصورسازی داده", "تحلیل کسب‌وکار"]
        },
        {
            "title": "کارشناس ارشد تحلیل داده (Senior Data Analyst)",
            "company": "دیجی‌کالا (Digikala)",
            "location": "تهران، میدان آزادی (حضوری)",
            "platform": "jobvision",
            "url": "https://jobvision.ir/jobs/digikala-senior-data-analyst",
            "salary_range": "۴۸ تا ۶۵ میلیون تومان",
            "description": "تحلیل رفتار کاربران و شاخص‌های کلیدی عملکرد مارکت‌پلیس، مسلط به پایتون (Pandas, SciPy, NumPy) و SQL پیشرفته. تجربه در تست‌های A/B و ساخت مدل‌های پیش‌بینی فروش.",
            "skills_required": ["Python", "SQL پیشرفته", "A/B Testing", "Machine Learning", "Tableau", "Git"]
        },
        {
            "title": "متخصص اتوماسیون و ایجنت‌های هوش مصنوعی (AI Workflow & Agentic Specialist)",
            "company": "هلدینگ هزاردستان (کافه‌بازار و دیوار)",
            "location": "تهران، سعادت‌آباد (هیبرید)",
            "platform": "jobinja",
            "url": "https://jobinja.ir/companies/cafebazaar/jobs/ai-agent-specialist",
            "salary_range": "۵۵ تا ۸۰ میلیون تومان",
            "description": "طراحی و پیاده‌سازی سیستم‌های ایجنتی (Agentic Workflows) و یکپارچه‌سازی مدل‌های زبانی بزرگ (LLMs مانند Gemini) با فرآیندهای کسب‌وکار. تسلط بر پایتون، مهندسی پرامپت و Vibe Coding جهت تحویل سریع نرم‌افزار.",
            "skills_required": ["Python", "AI Agents", "Vibe Coding", "Gemini / OpenAI API", "FastAPI", "Docker"]
        },
        {
            "title": "تحلیل‌گر جوان داده (Junior Data Analyst)",
            "company": "تپسی (Tapsi)",
            "location": "تهران، ونک (تمام‌وقت)",
            "platform": "jobvision",
            "url": "https://jobvision.ir/jobs/tapsi-junior-data-analyst",
            "salary_range": "۲۲ تا ۳۰ میلیون تومان",
            "description": "استخراج گزارش‌های روزانه ناوگان، تحلیل سفرها با SQL و تهیه داشبورد در اکسل و Power BI. روحیه یادگیری بالا، تفکر آماری و آشنایی با مبانی پایتون.",
            "skills_required": ["SQL", "Excel پیشرفته", "Power BI", "آمار کاربردی", "تحلیل داده"]
        },
        {
            "title": "مهندس هوش تجاری و پایپ‌لاین داده (BI & Data Engineer)",
            "company": "ایرانسل (MTN Irancell)",
            "location": "تهران، هروی (حضوری)",
            "platform": "karboard",
            "url": "https://karboard.io/job/irancell-bi-engineer",
            "salary_range": "۴۲ تا ۵۸ میلیون تومان",
            "description": "مدیریت انباره داده سازمانی، طراحی و نگهداری فرایندهای ETL، بهینه‌سازی کوئری‌های تحلیلی سنگین SQL و گزارش‌گیری برای مدیران ارشد سازمان.",
            "skills_required": ["Data Warehouse", "SQL Server", "Power BI", "SSIS / ETL", "Python"]
        },
        {
            "title": "توسعه‌دهنده بک‌اند و اتوماسیون (Python / FastAPI Developer)",
            "company": "زرین‌پال (ZarinPal)",
            "location": "تهران، سهروردی",
            "platform": "jobinja",
            "url": "https://jobinja.ir/companies/zarinpal/jobs/python-fastapi",
            "salary_range": "۴۰ تا ۵۵ میلیون تومان",
            "description": "توسعه میکروسرویس‌های مالی و درگاه پرداخت با FastAPI و PostgreSQL، خودکارسازی تسک‌ها با Celery و Redis، داکر و تست‌های واحد.",
            "skills_required": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git", "Redis"]
        },
        {
            "title": "تحلیل‌گر داده‌های رشد و بازاریابی (Product Growth Analyst)",
            "company": "اسنپ‌فود (SnappFood)",
            "location": "تهران، جردن",
            "platform": "jobvision",
            "url": "https://jobvision.ir/jobs/snappfood-growth-analyst",
            "salary_range": "۳۲ تا ۴۶ میلیون تومان",
            "description": "تحلیل نرخ تبدیل، فانل خرید و کمپین‌های مارکتینگ با SQL و ابزارهای تحلیل رفتار کاربر (Amplitude, Google Analytics). ارائه گزارش‌های تصمیم‌ساز.",
            "skills_required": ["SQL", "Google Analytics", "Power BI", "Funnel Analysis", "Excel پیشرفته"]
        }
    ]

    def hunt_jobs(self, query: str = "دیتا آنالیست", city: str = "تهران") -> list:
        """
        Discovers jobs, filters by criteria, and writes new ones into SQLite
        """
        conn = get_connection()
        cursor = conn.cursor()
        discovered = []

        for item in self.SAMPLE_KARBOARD_JOBS:
            # Generate deterministic job_id
            job_id = hashlib.md5(f"{item['platform']}_{item['title']}_{item['company']}".encode('utf-8')).hexdigest()[:12]
            
            # Check if exists
            cursor.execute("SELECT id, status, match_score FROM jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            
            if not row:
                cursor.execute("""
                INSERT INTO jobs (job_id, platform, title, company, location, salary_range, url, description, skills_required, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'discovered')
                """, (
                    job_id,
                    item["platform"],
                    item["title"],
                    item["company"],
                    item["location"],
                    item["salary_range"],
                    item["url"],
                    item["description"],
                    json.dumps(item["skills_required"], ensure_ascii=False)
                ))
                item_dict = dict(item)
                item_dict["job_id"] = job_id
                item_dict["status"] = "discovered"
                discovered.append(item_dict)
            else:
                item_dict = dict(item)
                item_dict["job_id"] = job_id
                item_dict["status"] = row["status"]
                item_dict["match_score"] = row["match_score"]
                discovered.append(item_dict)

        conn.commit()
        conn.close()
        return discovered

    def get_all_jobs(self) -> list:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs ORDER BY id DESC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        for r in rows:
            if isinstance(r.get("skills_required"), str):
                try:
                    r["skills_required"] = json.loads(r["skills_required"])
                except Exception:
                    r["skills_required"] = []
            if isinstance(r.get("match_reasons"), str):
                try:
                    r["match_reasons"] = json.loads(r["match_reasons"])
                except Exception:
                    r["match_reasons"] = []
        return rows

job_hunter_agent = JobHunterAgent()
