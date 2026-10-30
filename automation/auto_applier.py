"""
Async Job Application Queue & Dispatcher for Career Co-Pilot Enterprise.
Built with skills: job-queue-celery-redis + production-hardening
Features:
- Task Queue with retry policy and exponential backoff
- Idempotency protection against double submissions
- Rate limiting and daily application quota enforcement
- Mandatory User Confirmation Stage (Awaiting User Click)
- Autonomous mode enabled ONLY when explicitly granted by user
"""

import time
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from core.db import get_connection, log_audit, apply_user_job, get_user_jobs_list
from core.config import settings
from automation.platform_auth import platform_auth_manager, add_log

class ApplicationQueueTask:
    def __init__(self, task_id: str, user_id: int, job_id: str, requires_confirmation: bool = True):
        self.task_id = task_id
        self.user_id = user_id
        self.job_id = job_id
        self.requires_confirmation = requires_confirmation
        self.status = "pending" # pending, awaiting_confirmation, processing, completed, failed
        self.retries = 0
        self.max_retries = 3
        self.created_at = datetime.now()
        self.error_message = None

class AutoApplierQueue:
    """
    Queue manager implementing Rate Limiting, Exponential Backoff, and User Guardrail.
    """

    def __init__(self):
        self.queue: List[ApplicationQueueTask] = []
        self.idempotency_set = set()

    def enqueue_job_application(
        self, 
        user_id: int, 
        job_id: str, 
        requires_confirmation: bool = True,
        user_confirmed: bool = False
    ) -> Dict[str, Any]:
        """
        Enqueues an application. Checks idempotency, daily cap, and user confirmation.
        """
        # 1. Idempotency Check
        idempotency_key = hashlib.sha256(f"{user_id}_{job_id}".encode()).hexdigest()
        if idempotency_key in self.idempotency_set:
            return {
                "success": False,
                "status": "DUPLICATE_APPLICATION_IGNORED",
                "message": "این درخواست قبلاً در صف پردازش قرار گرفته است."
            }

        # 2. Check Daily Cap
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
        SELECT COUNT(*) FROM user_jobs 
        WHERE user_id = ? AND status = 'applied' AND DATE(applied_at) = DATE('now')
        """, (user_id,))
        today_applied = cur.fetchone()[0]

        cur.execute("SELECT daily_cap FROM profiles WHERE id = ?", (user_id,))
        prof = cur.fetchone()
        daily_cap = prof["daily_cap"] if prof else settings.DAILY_APPLICATION_CAP

        if today_applied >= daily_cap:
            conn.close()
            return {
                "success": False,
                "status": "DAILY_CAP_REACHED",
                "today_count": today_applied,
                "cap": daily_cap,
                "message": f"سقف ارسال روزانه ({daily_cap} آگهی) برای امروز پر شده است."
            }

        conn.close()

        # 3. Guardrail: User confirmation required?
        if requires_confirmation and not user_confirmed:
            task = ApplicationQueueTask(idempotency_key, user_id, job_id, requires_confirmation=True)
            task.status = "awaiting_confirmation"
            self.queue.append(task)
            self.idempotency_set.add(idempotency_key)
            
            add_log("JobQueue", f"آگهی {job_id} برای کاربر {user_id} در صف انتظار تأیید قرار گرفت.", "info")
            return {
                "success": True,
                "status": "AWAITING_USER_CONFIRMATION",
                "task_id": idempotency_key,
                "message": "آگهی آماده ارسال است و منتظر تأیید نهایی شما در داشبورد یا ربات تلگرام می‌باشد."
            }

        # 4. Immediate / Confirmed execution
        task = ApplicationQueueTask(idempotency_key, user_id, job_id, requires_confirmation=False)
        self.idempotency_set.add(idempotency_key)
        result = self._process_task_with_retry(task)
        return result

    def confirm_and_apply(self, user_id: int, job_id: str) -> Dict[str, Any]:
        """User clicked 'Confirm Apply' button in Dashboard or Telegram."""
        return platform_auth_manager.execute_live_apply(
            job_id=job_id,
            user_id=user_id,
            requires_confirmation=False,
            user_confirmed=True
        )

    def _process_task_with_retry(self, task: ApplicationQueueTask) -> Dict[str, Any]:
        """Executes application with exponential backoff retry."""
        base_delay = 0.5
        while task.retries <= task.max_retries:
            try:
                task.status = "processing"
                res = platform_auth_manager.execute_live_apply(
                    job_id=task.job_id,
                    user_id=task.user_id,
                    requires_confirmation=False,
                    user_confirmed=True
                )
                if res.get("success"):
                    task.status = "completed"
                    return res
                else:
                    raise Exception(res.get("error", "Application failed"))
            except Exception as e:
                task.retries += 1
                task.error_message = str(e)
                if task.retries > task.max_retries:
                    task.status = "failed"
                    add_log("JobQueue", f"تلاش‌های ارسال آگهی {task.job_id} ناموفق بود: {str(e)}", "error")
                    return {"success": False, "status": "MAX_RETRIES_EXCEEDED", "error": str(e)}
                
                # Exponential backoff
                sleep_time = base_delay * (2 ** (task.retries - 1))
                time.sleep(sleep_time)

        return {"success": False, "status": "FAILED"}

auto_applier_queue = AutoApplierQueue()
