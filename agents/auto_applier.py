import time
import random
from datetime import datetime
from core.db import get_connection

class AutoApplierAgent:
    """
    Agent responsible for:
    - Executing human-like application submissions
    - Enforcing daily application limits (e.g. max 15 per day)
    - Recording application logs and updating status in SQLite
    """

    def apply_to_job(self, job_id: str, user_id: int = 1) -> dict:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Check daily cap
        cursor.execute("""
        SELECT COUNT(*) FROM jobs 
        WHERE status = 'applied' AND date(applied_at) = date('now')
        """)
        today_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT daily_cap FROM profiles WHERE id = ?", (user_id,))
        cap_row = cursor.fetchone()
        daily_cap = cap_row["daily_cap"] if cap_row else 15

        if today_count >= daily_cap:
            conn.close()
            return {
                "success": False,
                "error": f"سقف ارسال روزانه ({daily_cap} رزومه) تکمیل شده است. برای رعایت رفتار انسانی و حفظ امنیت حساب، بقیه موارد فردا ارسال می‌شوند."
            }

        # 2. Check job status
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        job = cursor.fetchone()
        if not job:
            conn.close()
            return {"success": False, "error": "آگهی یافت نشد."}

        if job["status"] == "applied":
            conn.close()
            return {"success": False, "error": "رزومه برای این آگهی قبلاً ارسال شده است و شناسه آن قفل می‌باشد."}

        # 3. Simulate human delay
        delay = random.uniform(1.5, 3.5)
        time.sleep(delay)

        # 4. Mark as applied
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        UPDATE jobs
        SET status = 'applied',
            applied_at = ?
        WHERE job_id = ?
        """, (now_str, job_id))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "job_id": job_id,
            "title": job["title"],
            "company": job["company"],
            "applied_at": now_str,
            "platform": job["platform"],
            "message": f"رزومه با موفقیت برای شرکت {job['company']} ارسال شد."
        }

auto_applier_agent = AutoApplierAgent()
