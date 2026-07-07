from __future__ import annotations

import unittest

from ampbrowser.adapters import ADAPTERS, adapter_for
from ampbrowser.transports import inspect_transport


class AdaptersTest(unittest.TestCase):
    def test_known_adapters_are_registered(self) -> None:
        self.assertEqual({"tor", "i2p", "ipfs", "reticulum", "gemini"}, set(ADAPTERS))

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
        self.assertEqual(
            (
                "install or bundle Arti/Tor provider",
                "start managed Arti SOCKS proxy",
                "wait for socks5://127.0.0.1:9050",
            ),
            adapter.setup_steps(installed=False, platform="desktop"),
        )

    def test_ios_tor_adapter_prefers_foreground_arti_session(self) -> None:
        adapter = adapter_for("tor")

        self.assertIsNotNone(adapter)
        self.assertEqual(
            (
                "start foreground-only iOS Arti client session",
                "attach in-app onion networking bridge",
                "wait for in-app Tor readiness",
            ),
            adapter.setup_steps(installed=True, platform="ios"),
        )

    def test_ipfs_adapter_declares_gateway_not_anonymity(self) -> None:
        adapter = adapter_for("ipfs")

        self.assertIsNotNone(adapter)
        self.assertEqual("http://127.0.0.1:8080", adapter.endpoint)
        self.assertIn("not an anonymity layer", adapter.note)


if __name__ == "__main__":
    unittest.main()
