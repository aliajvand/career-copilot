"""
Unified Interactive Browser Login Helper for Career Co-Pilot.
Spawns a visible Microsoft Edge browser session for Jobvision or Jobinja,
allows the user to complete 2FA, OTP SMS, or Captcha directly in the browser,
and automatically extracts and persists the authenticated session state.
"""

import threading
import time
import json
from pathlib import Path
from typing import Dict, Any

from playwright.sync_api import sync_playwright
from core.db import get_connection, log_audit
from automation.platform_auth import SessionCrypto, add_log

SESSION_DIR = Path("data")

class InteractiveLoginManager:
    _active_threads: Dict[str, threading.Thread] = {}

    @classmethod
    def is_logging_in(cls, platform: str) -> bool:
        t = cls._active_threads.get(platform)
        return t is not None and t.is_alive()

    @classmethod
    def launch_browser_login_async(cls, platform: str, phone: str = "09195253462"):
        if cls.is_logging_in(platform):
            return {"success": False, "message": f"یک فرآیند ورود برای {platform} هم‌اکنون در حال اجرا است."}

        thread = threading.Thread(
            target=cls._run_login_worker,
            args=(platform, phone),
            daemon=True
        )
        cls._active_threads[platform] = thread
        thread.start()
        return {"success": True, "message": f"مرورگر برای ورود به {platform} با موفقیت باز شد."}

    @classmethod
    def _run_login_worker(cls, platform: str, phone: str):
        session_file = SESSION_DIR / f"{platform}_session.json"
        session_file.parent.mkdir(parents=True, exist_ok=True)

        target_url = "https://account.jobvision.ir/Candidate" if platform == "jobvision" else "https://jobinja.ir/login/user"
        plat_fa = "جاب‌ویژن" if platform == "jobvision" else "جابینجا"

        add_log("BrowserLogin", f"پنجره مرورگر برای ورود کاربر به {plat_fa} باز شد...", "info")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False, channel="msedge")
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 850}
                )
                page = context.new_page()
                page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

                # Pre-fill phone/username if possible
                try:
                    if platform == "jobvision":
                        page.wait_for_selector("input[name='Username']", timeout=5000)
                        page.fill("input[name='Username']", phone)
                    elif platform == "jobinja":
                        page.wait_for_selector("input[name='identifier'], input[type='email'], input[name='email']", timeout=5000)
                        page.fill("input[name='identifier'], input[type='email'], input[name='email']", phone)
                except Exception:
                    pass

                # Wait up to 3 minutes for human completion
                max_wait = 180
                start_time = time.time()
                logged_in = False

                while time.time() - start_time < max_wait:
                    curr_url = page.url.lower()
                    if platform == "jobvision":
                        if "jobvision.ir" in curr_url and "account.jobvision.ir" not in curr_url:
                            logged_in = True
                            break
                        elif "candidate/summary" in curr_url or "candidate/profile" in curr_url:
                            logged_in = True
                            break
                    elif platform == "jobinja":
                        if "jobinja.ir" in curr_url and "login" not in curr_url:
                            logged_in = True
                            break

                    time.sleep(1.5)

                if logged_in:
                    context.storage_state(path=str(session_file))
                    cookies = context.cookies()
                    encrypted_cookies = SessionCrypto.encrypt(json.dumps(cookies))

                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("""
                    INSERT INTO accounts (platform, username_or_email, phone_number, session_cookies, status, last_login_at, updated_at)
                    VALUES (?, ?, ?, ?, 'connected', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(platform) DO UPDATE SET
                        session_cookies = excluded.session_cookies,
                        status = 'connected',
                        last_login_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    """, (platform, phone, phone, encrypted_cookies))
                    conn.commit()
                    conn.close()

                    add_log("BrowserLogin", f"ورود به {plat_fa} موفقیت‌آمیز بود و سشن دائمی ذخیره گردید.", "success")
                    log_audit(1, "interactive_login_success", "account", platform)
                    time.sleep(2)
                    browser.close()
                else:
                    add_log("BrowserLogin", f"مهلت زمان ورود به {plat_fa} منقضی شد یا پنجره بسته شد.", "warning")
                    try:
                        browser.close()
                    except Exception:
                        pass

        except Exception as e:
            add_log("BrowserLogin", f"خطا در اجرای مرورگر ورود {plat_fa}: {str(e)}", "error")

interactive_login_manager = InteractiveLoginManager()
