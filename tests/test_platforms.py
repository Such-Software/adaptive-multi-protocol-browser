from __future__ import annotations

import unittest

from ampbrowser.platforms import capability_for, normalize_platform


class PlatformsTest(unittest.TestCase):
    def test_android_tor_is_managed_setup_capable(self) -> None:
        capability = capability_for("tor", "android")

        self.assertEqual("android", capability.platform)
        self.assertEqual("planned", capability.manage)
        self.assertTrue(capability.can_manage_setup)

    def test_ios_tor_is_foreground_only(self) -> None:
        capability = capability_for("tor", "ios")

        self.assertEqual("foreground-only", capability.manage)
        self.assertTrue(capability.can_manage_setup)
        self.assertIn("foreground", capability.note)

    def test_ipfs_android_is_gateway_first_planned(self) -> None:
        capability = capability_for("ipfs", "android")

        self.assertEqual("planned", capability.manage)
        self.assertIn("gateway-first", capability.note)

    def test_unknown_platform_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            normalize_platform("watch")


if __name__ == "__main__":
    unittest.main()
