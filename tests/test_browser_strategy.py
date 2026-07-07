from __future__ import annotations

import unittest

from ampbrowser.metadata import BROWSER_BACKENDS


class BrowserStrategyTest(unittest.TestCase):
    def test_primary_desktop_backend_is_bundled_gecko(self) -> None:
        primary = [backend for backend in BROWSER_BACKENDS if backend.role == "primary desktop runtime"]

        self.assertEqual(1, len(primary))
        self.assertEqual("ampb-gecko-desktop", primary[0].name)
        self.assertIn("no system browser dependency", primary[0].privacy_posture)

    def test_primary_android_backend_is_bundled_geckoview(self) -> None:
        primary = [backend for backend in BROWSER_BACKENDS if backend.role == "primary android runtime"]

        self.assertEqual(1, len(primary))
        self.assertEqual("ampb-geckoview-android", primary[0].name)
        self.assertIn("no system browser dependency", primary[0].privacy_posture)


if __name__ == "__main__":
    unittest.main()
