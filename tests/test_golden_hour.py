import unittest
from datetime import datetime
from agents.golden_hour import golden_hour_engine, golden_hour_scheduler

class TestGoldenHourEngine(unittest.TestCase):

    def test_experiment_slot_assignment(self):
        slot = golden_hour_engine.assign_experiment_slot(user_id=1, job_id="job_gh_test_1")
        self.assertIn(slot, ["morning_golden", "midday", "afternoon"])

    def test_record_outcome_and_ab_eval(self):
        golden_hour_engine.assign_experiment_slot(user_id=1, job_id="job_gh_test_2")
        golden_hour_engine.record_outcome("job_gh_test_2", user_id=1, outcome="interview")
        results = golden_hour_engine.evaluate_ab_results()
        self.assertIn("slot_breakdown", results)
        self.assertIn("hypothesis", results)

    def test_scheduler_configurable_window(self):
        golden_hour_scheduler.update_window(9, 11)
        self.assertEqual(golden_hour_scheduler.start_hour, 9)
        self.assertEqual(golden_hour_scheduler.end_hour, 11)
        # Check Saturday morning
        test_dt = datetime(2026, 10, 31, 10, 0, 0) # Saturday 10:00 AM
        self.assertTrue(golden_hour_scheduler.is_currently_in_window(test_dt))

if __name__ == "__main__":
    unittest.main()
