"""Synthetic negative tests to prove the static gate actually fails closed."""
import unittest
from phase9_security_gate import check_sources

MANIFEST = '<application android:allowBackup="false" android:usesCleartextTraffic="false" />'
GRADLE = 'targetSdk 35\nrelease { minifyEnabled true; debuggable false; proguardFiles "rules.pro" }'
NATIVE = 'constexpr char prefix[] = "https://"; path = "/healthz";'
AUTH = 'allow_legacy_plaintext_notes: bool = False'


class Phase9StaticGateTests(unittest.TestCase):
    def test_good_synthetic_policy(self):
        self.assertEqual(check_sources(MANIFEST, GRADLE, NATIVE, AUTH), [])

    def test_backup_or_plaintext_downgrade_rejected(self):
        self.assertTrue(check_sources(MANIFEST.replace('"false"', '"true"', 1),
                                      GRADLE, NATIVE, AUTH))
        self.assertTrue(check_sources(MANIFEST.replace('usesCleartextTraffic="false"',
                                                      'usesCleartextTraffic="true"'),
                                      GRADLE, NATIVE, AUTH))

    def test_debuggable_release_and_unminified_rejected(self):
        self.assertTrue(check_sources(MANIFEST, GRADLE.replace("debuggable false", "debuggable true"),
                                      NATIVE, AUTH))
        self.assertTrue(check_sources(MANIFEST, GRADLE.replace("minifyEnabled true", "minifyEnabled false"),
                                      NATIVE, AUTH))

    def test_tls_bypass_and_plaintext_demo_default_rejected(self):
        self.assertTrue(check_sources(MANIFEST, GRADLE, NATIVE + " SSL_VERIFY_NONE", AUTH))
        self.assertTrue(check_sources(MANIFEST, GRADLE, NATIVE,
                                      AUTH.replace("= False", "= True")))


if __name__ == "__main__":
    unittest.main()
