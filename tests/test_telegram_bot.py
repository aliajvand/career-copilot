import unittest
from core.db import init_db, get_connection
from telegram_bot import get_or_create_user, format_user_status, format_user_jobs

class TestTelegramBotFeatures(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_user_creation_and_recommender(self):
        profile = get_or_create_user(telegram_id=987654321, full_name="کاربر تست تلگرام")
        self.assertIn("id", profile)

        status_text = format_user_status(profile)
        self.assertIn("کاربر تست تلگرام", status_text)

        jobs_text = format_user_jobs(profile)
        self.assertIn("دلیل پیشنهاد", jobs_text)

    def test_sandbox_transaction_record(self):
        import uuid
        test_auth = f"zarinpal_sandbox_{uuid.uuid4().hex[:8]}"
        test_idem = f"idem_{uuid.uuid4().hex[:8]}"

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO transactions (user_id, authority, amount, status, gateway, idempotency_key, description)
        VALUES (1, ?, 199000, 'pending', 'zarinpal_sandbox', ?, 'تست پرداخت')
        """, (test_auth, test_idem))
        conn.commit()

        cur.execute("SELECT status, amount FROM transactions WHERE authority = ?", (test_auth,))
        row = cur.fetchone()
        self.assertEqual(row["status"], "pending")
        self.assertEqual(row["amount"], 199000)
        conn.close()

if __name__ == "__main__":
    unittest.main()
