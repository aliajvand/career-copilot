import unittest
from agents.job_hunter import job_hunter_agent, EthicalScraperHelper

class TestJobHunterAgent(unittest.TestCase):

    def test_ethical_scraper_rules(self):
        can_fetch, reason = EthicalScraperHelper.can_fetch("https://jobinja.ir/jobs")
        self.assertFalse(can_fetch)
        self.assertIn("CLOUDFLARE", reason)

        can_fetch_jv, reason_jv = EthicalScraperHelper.can_fetch("https://jobvision.ir/jobs")
        self.assertTrue(can_fetch_jv)

    def test_source_diagnostics_honesty(self):
        diag = job_hunter_agent.get_source_diagnostics()
        self.assertGreater(len(diag), 0)
        jobinja_diag = next((d for d in diag if d["platform"] == "jobinja"), None)
        self.assertIsNotNone(jobinja_diag)
        self.assertIn("BLOCKED", jobinja_diag["status"])

    def test_hunt_jobs_provenance(self):
        jobs = job_hunter_agent.hunt_jobs()
        self.assertGreater(len(jobs), 0)
        first = jobs[0]
        self.assertIn("source_type", first)
        self.assertIn("job_id", first)

if __name__ == "__main__":
    unittest.main()
