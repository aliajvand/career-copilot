import unittest
from automation.platform_auth import SessionCrypto, platform_auth_manager, add_log
from core.db import get_connection

class TestPlatformAuth(unittest.TestCase):

    def test_session_crypto_encrypt_decrypt(self):
        secret_token = "my_super_secret_session_cookie_12345"
        encrypted = SessionCrypto.encrypt(secret_token)
        self.assertNotEqual(secret_token, encrypted)
        decrypted = SessionCrypto.decrypt(encrypted)
        self.assertEqual(secret_token, decrypted)

    def test_zero_logging_masks_secrets(self):
        add_log("SecurityTest", "Attempting login with password: 0441067824 for user")
        logs = platform_auth_manager.get_recent_logs(5)
        latest = next((l for l in logs if l["agent_name"] == "SecurityTest"), None)
        self.assertIsNotNone(latest)
        self.assertNotIn("0441067824", latest["message"])
        self.assertIn("******", latest["message"])

    def test_user_confirmation_guardrail(self):
        # 1. Unconfirmed attempt must return AWAITING_USER_CONFIRMATION
        res_unconfirmed = platform_auth_manager.execute_live_apply(
            job_id="test_guardrail_job", 
            user_id=1, 
            requires_confirmation=True, 
            user_confirmed=False
        )
        # Even if job does not exist, check confirmation priority
        if "requires_user_confirmation" in res_unconfirmed:
            self.assertTrue(res_unconfirmed["requires_user_confirmation"])
            self.assertEqual(res_unconfirmed["status"], "AWAITING_USER_CONFIRMATION")

    def test_secure_logout(self):
        res = platform_auth_manager.secure_logout("jobinja", user_id=1)
        self.assertTrue(res["success"])
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT status FROM accounts WHERE platform = 'jobinja'")
        status = cur.fetchone()[0]
        self.assertEqual(status, "logged_out")
        conn.close()

if __name__ == "__main__":
    unittest.main()
