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
        self.assertIn("Recommender", jobs_text)

    def test_sandbox_transaction_record(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO transactions (user_id, authority, amount, status, gateway, idempotency_key, description)
        VALUES (1, 'zarinpal_sandbox_test_123', 199000, 'pending', 'zarinpal_sandbox', 'idem_key_123', 'تست پرداخت')
        """)
        conn.commit()

        cur.execute("SELECT status, amount FROM transactions WHERE authority = 'zarinpal_sandbox_test_123'")
        row = cur.fetchone()
        self.assertEqual(row["status"], "pending")
        self.assertEqual(row["amount"], 199000)
        conn.close()

if __name__ == "__main__":
    unittest.main()
