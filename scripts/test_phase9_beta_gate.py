import unittest
from phase9_beta_gate import REQUIRED_CHECKS, validate_beta_report


class BetaGateTests(unittest.TestCase):
    def test_empty_report_blocked(self):
        self.assertTrue(validate_beta_report({"schema_version": 1, "checks": {}}))

    def test_synthetic_complete_checklist_logic(self):
        # Algorithm test only, NOT release approval or evidence of completed beta.
        fake = {
            "schema_version": 1,
            "checks": {
                x: {
                    "status": "passed",
                    "evidence": "https://github.com/Gh0stDeveloper/smart-uni/actions/runs/12345",
                    "reviewed_by": "synthetic-reviewer",
                } for x in REQUIRED_CHECKS
            },
            "blocking_critical_findings": 0,
            "publication_approval": True,
        }
        self.assertEqual(validate_beta_report(fake), [])
        fake["checks"]["android_physical"]["status"] = "blocked"
        self.assertTrue(validate_beta_report(fake))
        fake["checks"]["android_physical"]["status"] = "passed"
        fake["blocking_critical_findings"] = 1
        self.assertTrue(validate_beta_report(fake))


if __name__ == "__main__":
    unittest.main()
