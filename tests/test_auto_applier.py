import unittest
from automation.auto_applier import auto_applier_queue
from core.db import init_db

class TestAutoApplierQueue(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_idempotency_and_confirmation(self):
        # 1. Enqueue without user confirmation
        res1 = auto_applier_queue.enqueue_job_application(
            user_id=1,
            job_id="test_queue_job_101",
            requires_confirmation=True,
            user_confirmed=False
        )
        self.assertTrue(res1["success"])
        self.assertEqual(res1["status"], "AWAITING_USER_CONFIRMATION")

        # 2. Second attempt must be caught by idempotency
        res2 = auto_applier_queue.enqueue_job_application(
            user_id=1,
            job_id="test_queue_job_101",
            requires_confirmation=True,
            user_confirmed=False
        )
        self.assertFalse(res2["success"])
        self.assertEqual(res2["status"], "DUPLICATE_APPLICATION_IGNORED")

    def test_confirm_and_apply(self):
        res = auto_applier_queue.confirm_and_apply(user_id=1, job_id="test_queue_job_102")
        # If job does not exist in DB, it returns gracefully without crashing
        self.assertIn("success", res)

if __name__ == "__main__":
    unittest.main()
