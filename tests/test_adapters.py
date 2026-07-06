from __future__ import annotations

import unittest

from ampbrowser.adapters import ADAPTERS, adapter_for
from ampbrowser.transports import inspect_transport


class AdaptersTest(unittest.TestCase):
    def test_known_adapters_are_registered(self) -> None:
        self.assertEqual({"tor", "i2p", "reticulum", "gemini"}, set(ADAPTERS))

    def test_gemini_adapter_is_builtin_ready(self) -> None:
        status = inspect_transport("gemini")

        self.assertIsNotNone(status)
        self.assertTrue(status.installed)
        self.assertTrue(status.running)
        self.assertTrue(status.adoptable)

    def test_tor_adapter_setup_steps_respect_ownership_language(self) -> None:
        adapter = adapter_for("tor")

        self.assertIsNotNone(adapter)
        self.assertEqual("stop only AMPB-owned Tor daemon", adapter.stop_policy)
        self.assertEqual(("install Tor provider", "start managed Tor daemon", "wait for socks5://127.0.0.1:9050"), adapter.setup_steps(installed=False, platform="desktop"))


if __name__ == "__main__":
    unittest.main()
