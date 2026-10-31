"""
Interactive Jobvision Login Helper.
Launches a visible browser window, navigates to Jobvision candidate login,
enters username, and waits for user to solve ARCaptcha.
Once logged in, it exports the session to data/jobvision_session.json so that
future applications can run fully automatically.
"""

import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

from core.db import get_connection, log_audit
from automation.platform_auth import SessionCrypto, add_log

sys.stdout.reconfigure(encoding='utf-8')

SESSION_FILE = Path("data/jobvision_session.json")

def interactive_login(timeout_seconds: int = 120):
    print("=" * 60)
    print("=== دستیار ورود واقعی به جاب‌ویژن (Jobvision Auth Helper) ===")
    print("=" * 60)
    print("مرورگر Edge در حال باز شدن است...")
    print("لطفاً در صفحه باز شده، در صورت درخواست، کپچای امنیتی را حل نموده و وارد حساب شوید.")
    print(f"حداکثر زمان انتظار: {timeout_seconds} ثانیه")
    print("-" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="msedge")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 850}
        )
        page = context.new_page()

        try:
            page.goto("https://account.jobvision.ir/Candidate", wait_until="domcontentloaded", timeout=30000)
            
            # Try to pre-fill mobile
            try:
                page.wait_for_selector("input[name='Username']", timeout=5000)
                page.fill("input[name='Username']", "09195253462")
                print("شماره موبایل 09195253462 وارد شد.")
            except Exception:
                pass

            start_time = time.time()
            logged_in = False

            while time.time() - start_time < timeout_seconds:
                curr_url = page.url.lower()
                # Check if redirected to main jobvision or profile
                if "jobvision.ir" in curr_url and "account.jobvision.ir" not in curr_url:
                    logged_in = True
                    break
                elif "candidate/summary" in curr_url or "candidate/profile" in curr_url:
                    logged_in = True
                    break
                
                time.sleep(1)

            if logged_in:
                print("\n[+] ورود موفقیت‌آمیز به جاب‌ویژن تایید شد!")
                SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
                context.storage_state(path=str(SESSION_FILE))
                print(f"[+] سشن کاربری در {SESSION_FILE} ذخیره گردید.")

                # Save encrypted into database
                cookies = context.cookies()
                encrypted_cookies = SessionCrypto.encrypt(json.dumps(cookies))
                conn = get_connection()
                c = conn.cursor()
                c.execute("""
                UPDATE accounts
                SET session_cookies = ?, status = 'connected', last_login_at = CURRENT_TIMESTAMP
                WHERE platform = 'jobvision'
                """, (encrypted_cookies,))
                conn.commit()
                conn.close()

                add_log("JobvisionAuth", "نشست کاربری جاب‌ویژن با موفقیت دریافت و فعال شد.", "success")
                print("سیستم اکنون آماده ارسال رزومه واقعی به تمام آگهی‌های انتخابی است.")
                time.sleep(2)
                browser.close()
                return True
            else:
                print("\n[-] مهلت زمان ورود به پایان رسید یا کاربر صفحه را بست.")
                browser.close()
                return False

        except Exception as e:
            print(f"\n[-] خطا در اجرا: {e}")
            try:
                browser.close()
            except Exception:
                pass
            return False

if __name__ == "__main__":
    interactive_login()
