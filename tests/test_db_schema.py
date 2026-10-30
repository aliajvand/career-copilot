import unittest
import sqlite3
from core.db import init_db, get_connection, log_audit, soft_delete_job, get_user_jobs_list, upsert_user_job

class TestDatabaseSchema(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_composite_indexes_exist(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("PRAGMA index_list('jobs')")
        indices = [row["name"] for row in cur.fetchall()]
        self.assertIn("idx_jobs_job_id", indices)
        self.assertIn("idx_jobs_created_status", indices)

        cur.execute("PRAGMA index_list('user_jobs')")
        user_indices = [row["name"] for row in cur.fetchall()]
        self.assertIn("idx_user_jobs_composite", user_indices)
        self.assertIn("idx_user_jobs_user_status", user_indices)
        conn.close()

    def test_audit_log(self):
        log_audit(user_id=1, action="test_login", entity_type="auth", changes={"status": "success"})
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM audit_logs WHERE action = 'test_login' ORDER BY id DESC LIMIT 1")
        row = dict(cur.fetchone() or {})
        self.assertEqual(row.get("user_id"), 1)
        self.assertEqual(row.get("action"), "test_login")
        conn.close()

    def test_soft_delete(self):
        upsert_user_job(user_id=1, job_id="test_soft_del", match_score=90, match_reasons=["test"], missing_skills=[], status="discovered")
        soft_delete_job("test_soft_del", user_id=1)
        active_jobs = get_user_jobs_list(user_id=1, limit=50, include_deleted=False)
        job_ids = [j["job_id"] for j in active_jobs]
        self.assertNotIn("test_soft_del", job_ids)

if __name__ == "__main__":
    unittest.main()
