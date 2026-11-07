import copy
import unittest
from phase9_lockfile_gate import verify_npm, verify_cargo


class LockfileGateTests(unittest.TestCase):
    def setUp(self):
        self.package = {"name": "smartuni-portal", "version": "0.1.0",
                        "dependencies": {"next": "16.4.5"}, "devDependencies": {}}
        self.npm = {"lockfileVersion": 3, "packages": {
            "": copy.deepcopy(self.package),
            "node_modules/next": {"integrity": "sha512-YWJj", "version": "16.4.5"},
        }}
        self.cargo = {"package": {"name": "smartuni-core", "version": "0.1.0"}}
        self.cargo_lock = {"version": 3, "package": [
            {"name": "smartuni-core", "version": "0.1.0"},
            {"name": "serde", "version": "1.0.0", "source": "registry+index", "checksum": "f" * 64},
        ]}

    def test_positive_fixture(self):
        self.assertEqual(verify_npm(self.package, self.npm), [])
        self.assertEqual(verify_cargo(self.cargo, self.cargo_lock), [])

    def test_npm_manifest_drift_rejected(self):
        self.package["dependencies"]["next"] = "99.0.0"
        self.assertTrue(verify_npm(self.package, self.npm))

    def test_npm_checksum_missing_rejected(self):
        self.npm["packages"]["node_modules/next"].pop("integrity")
        self.assertTrue(verify_npm(self.package, self.npm))

    def test_cargo_checksum_missing_rejected(self):
        self.cargo_lock["package"][1].pop("checksum")
        self.assertTrue(verify_cargo(self.cargo, self.cargo_lock))

    def test_cargo_version_drift_rejected(self):
        self.cargo["package"]["version"] = "0.2.0"
        self.assertTrue(verify_cargo(self.cargo, self.cargo_lock))


if __name__ == "__main__":
    unittest.main()
