import unittest
from phase9_beta_gate import REQUIRED_CHECKS, validate_beta_report, verify_actions_evidence


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

    def test_github_success_is_checked_against_exact_main_commit(self):
        sha = "b" * 40
        report = {
            "release_commit": sha,
            "checks": {
                "android_instrumentation": {
                    "status": "passed",
                    "evidence": "https://github.com/Gh0stDeveloper/smart-uni/actions/runs/12345",
                    "reviewed_by": "synthetic",
                },
            },
        }

        def successful(run_id):
            return {
                "id": run_id,
                "repository": {"full_name": "Gh0stDeveloper/smart-uni"},
                "head_sha": sha,
                "head_branch": "main",
                "status": "completed",
                "conclusion": "success",
            }

        self.assertEqual(verify_actions_evidence(report, successful), [])
        self.assertTrue(verify_actions_evidence(report,
                        lambda run_id: {**successful(run_id), "conclusion": "failure"}))
        self.assertTrue(verify_actions_evidence(report,
                        lambda run_id: {**successful(run_id), "head_sha": "a" * 40}))
        self.assertTrue(verify_actions_evidence(report,
                        lambda run_id: {**successful(run_id), "head_branch": "dev"}))
        report["release_commit"] = ""
        self.assertTrue(verify_actions_evidence(report, successful))


if __name__ == "__main__":
    unittest.main()
