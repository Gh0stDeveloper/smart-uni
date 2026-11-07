import copy
import tempfile
import unittest
import zipfile
from pathlib import Path

from phase9_artifact_integrity import ArtifactRejected, build_receipt, verify_receipt


class ArtifactReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paths = {"synthetic_apk": "fake.apk"}
        self.artifact = self.root / "fake.apk"
        with zipfile.ZipFile(self.artifact, "w") as archive:
            archive.writestr("classes.dex", b"SYNTHETIC_ONLY" * 10)

    def test_roundtrip_receipt(self):
        receipt = build_receipt(self.root, "a" * 40, self.paths)
        self.assertFalse(receipt["release_approved"])
        verify_receipt(self.root, receipt, self.paths)

    def test_tamper_rejected(self):
        receipt = build_receipt(self.root, "a" * 40, self.paths)
        with self.artifact.open("ab") as handle:
            handle.write(b"tampered")
        with self.assertRaises(ArtifactRejected):
            verify_receipt(self.root, receipt, self.paths)

    def test_unsigned_only_policy(self):
        receipt = build_receipt(self.root, "a" * 40, self.paths)
        bad = copy.deepcopy(receipt)
        bad["release_approved"] = True
        with self.assertRaises(ArtifactRejected):
            verify_receipt(self.root, bad, self.paths)

    def test_invalid_commit_rejected(self):
        with self.assertRaises(ArtifactRejected):
            build_receipt(self.root, "fake", self.paths)

    def test_malformed_zip_rejected(self):
        self.artifact.write_bytes(b"non-zip content" * 10)
        with self.assertRaises(ArtifactRejected):
            build_receipt(self.root, "a" * 40, self.paths)


if __name__ == "__main__":
    unittest.main()
