from __future__ import annotations

import unittest

from ampbrowser.metadata import BROWSER_BACKENDS


class BrowserStrategyTest(unittest.TestCase):
    def test_primary_backend_is_hardened_firefox(self) -> None:
        primary = [backend for backend in BROWSER_BACKENDS if backend.role == "primary web runtime"]

        self.assertEqual(1, len(primary))
        self.assertEqual("hardened-firefox", primary[0].name)
        self.assertIn("Firefox", primary[0].privacy_posture)

    def test_chromium_is_fallback_not_privacy_baseline(self) -> None:
        chromium = next(backend for backend in BROWSER_BACKENDS if backend.name == "chromium-cef")

        self.assertEqual("fallback", chromium.status)
        self.assertIn("not a Tor Browser", chromium.privacy_posture)


if __name__ == "__main__":
    unittest.main()
