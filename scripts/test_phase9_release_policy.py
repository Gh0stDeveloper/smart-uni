import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from phase9_release_policy import ReleaseRejected, verify_release


class Phase9ReleasePolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.artifact = Path(self.temp.name) / "synthetic.apk"
        self.artifact.write_bytes(b"NOT_AN_APK synthetic artifact used only for verifier tests")
        self.secret = Ed25519PrivateKey.generate()
        self.public = self.secret.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.metadata = {
            "schema_version": 1,
            "package_name": "xyz.smartuni.app",
            "channel": "internal",
            "version_code": 9,
            "min_supported_version_code": 1,
            "artifact_sha256": hashlib.sha256(self.artifact.read_bytes()).hexdigest(),
            "artifact_size": self.artifact.stat().st_size,
            "source_commit": "a" * 40,
        }

    def check(self, *, version=8, minimum=1, metadata=None, artifact=None,
              corrupt_signature=False):
        raw = json.dumps(metadata or self.metadata, sort_keys=True, separators=(",", ":")).encode()
        signature = bytearray(self.secret.sign(raw))
        if corrupt_signature:
            signature[0] ^= 1
        return verify_release(raw, base64.b64encode(signature), self.public,
                              artifact or self.artifact,
                              installed_version_code=version,
                              min_allowed_version_code=minimum)

    def test_valid_signed_manifest_digest(self):
        self.assertEqual(self.check()["version_code"], 9)

    def test_tamper_and_invalid_signature_rejected(self):
        with self.assertRaises(ReleaseRejected):
            self.check(corrupt_signature=True)
        modified = dict(self.metadata)
        modified["channel"] = "production"
        raw = json.dumps(self.metadata, sort_keys=True).encode()
        signature = base64.b64encode(self.secret.sign(raw))
        tampered = json.dumps(modified, sort_keys=True).encode()
        with self.assertRaises(ReleaseRejected):
            verify_release(tampered, signature, self.public, self.artifact,
                           installed_version_code=8, min_allowed_version_code=1)

    def test_downgrade_and_policy_floor_rejected(self):
        with self.assertRaises(ReleaseRejected):
            self.check(version=10)
        with self.assertRaises(ReleaseRejected):
            self.check(minimum=10)
        with self.assertRaises(ReleaseRejected):
            self.check(metadata={**self.metadata, "version_code": 0})
        with self.assertRaises(ReleaseRejected):
            self.check(metadata={**self.metadata, "version_code": True})

    def test_same_signature_wrong_artifact_rejected(self):
        other = Path(self.temp.name) / "other.apk"
        other.write_bytes(b"tampered")
        with self.assertRaises(ReleaseRejected):
            self.check(artifact=other)

    def test_wrong_public_key_rejected(self):
        raw = json.dumps(self.metadata, sort_keys=True).encode()
        signature = base64.b64encode(self.secret.sign(raw))
        other = Ed25519PrivateKey.generate().public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        with self.assertRaises(ReleaseRejected):
            verify_release(raw, signature, other, self.artifact,
                           installed_version_code=8, min_allowed_version_code=1)


if __name__ == "__main__":
    unittest.main()
