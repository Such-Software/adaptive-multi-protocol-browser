from __future__ import annotations

import unittest
from unittest.mock import patch

from ampbrowser.config import AppConfig
from ampbrowser.launch import prepare_open
from ampbrowser.transports import TransportStatus


class PrepareOpenTest(unittest.TestCase):
    def test_clearnet_is_ready_without_consent(self) -> None:
        plan = prepare_open("wownero.org")

        self.assertEqual("ready", plan.status)
        self.assertFalse(plan.browse_plan.requires_consent)
        self.assertEqual(".ampb/profiles/clearnet", plan.profile_path)
        self.assertEqual("-", plan.proxy)

    def test_missing_i2p_requires_consent_before_setup(self) -> None:
        status = TransportStatus(
            transport="i2p",
            installed=False,
            running=False,
            endpoint="http://127.0.0.1:4444",
            adoptable=False,
            manage_supported=True,
            note="I2P HTTP proxy",
        )

        with patch("ampbrowser.plan.inspect_transport", return_value=status):
            plan = prepare_open("http://example.b32.i2p/")

        self.assertEqual("consent-required", plan.status)
        self.assertFalse(plan.consent_granted)
        self.assertEqual(
            ("install I2P provider", "start managed I2P router", "wait for http://127.0.0.1:4444"),
            plan.setup_steps,
        )
        self.assertIn("install and start", plan.message)

    def test_yes_approves_setup_without_executing_it(self) -> None:
        status = TransportStatus(
            transport="tor",
            installed=True,
            running=False,
            endpoint="socks5://127.0.0.1:9050",
            adoptable=False,
            manage_supported=True,
            note="Tor SOCKS proxy",
        )

        with patch("ampbrowser.plan.inspect_transport", return_value=status):
            plan = prepare_open("http://example.onion/", consent=True)

        self.assertEqual("setup-approved", plan.status)
        self.assertTrue(plan.dry_run)
        self.assertTrue(plan.consent_granted)
        self.assertEqual(("start managed Arti SOCKS proxy", "wait for socks5://127.0.0.1:9050"), plan.setup_steps)

    def test_custom_state_dir_changes_profile_path(self) -> None:
        config = AppConfig(state_dir=".local/ampb", transport_modes={})

        plan = prepare_open("wownero.org", config=config)

        self.assertEqual(".local/ampb/profiles/clearnet", plan.profile_path)

    def test_android_setup_steps_include_foreground_service(self) -> None:
        status = TransportStatus(
            transport="i2p",
            installed=False,
            running=False,
            endpoint="http://127.0.0.1:4444",
            adoptable=False,
            manage_supported=True,
            note="I2P HTTP proxy",
        )

        with patch("ampbrowser.plan.inspect_transport", return_value=status):
            plan = prepare_open("http://example.b32.i2p/", platform="android")

        self.assertEqual("android", plan.browse_plan.platform_capability.platform)
        self.assertEqual(
            (
                "install or enable Android i2p provider",
                "start visible Android foreground service for i2p",
                "start managed Android i2p transport",
                "wait for http://127.0.0.1:4444",
            ),
            plan.setup_steps,
        )

    def test_ipfs_desktop_setup_uses_gateway_adapter(self) -> None:
        status = TransportStatus(
            transport="ipfs",
            installed=False,
            running=False,
            endpoint="http://127.0.0.1:8080",
            adoptable=False,
            manage_supported=True,
            note="IPFS local gateway",
        )

        with patch("ampbrowser.plan.inspect_transport", return_value=status):
            plan = prepare_open("ipfs://bafyexample", consent=True)

        self.assertEqual("setup-approved", plan.status)
        self.assertEqual(
            ("install IPFS/Kubo provider", "start managed IPFS gateway", "wait for http://127.0.0.1:8080"),
            plan.setup_steps,
        )

    def test_ios_tor_setup_uses_bundled_arti_runtime(self) -> None:
        status = TransportStatus(
            transport="tor",
            installed=False,
            running=False,
            endpoint="socks5://127.0.0.1:9050",
            adoptable=False,
            manage_supported=True,
            note="Tor SOCKS proxy",
        )

        with patch("ampbrowser.plan.inspect_transport", return_value=status):
            plan = prepare_open("http://example.onion/", platform="ios")

        self.assertEqual("consent-required", plan.status)
        self.assertEqual(
            (
                "enable bundled iOS Arti Tor runtime",
                "start foreground-only iOS Arti client session",
                "attach in-app onion networking bridge",
                "wait for in-app Tor readiness",
            ),
            plan.setup_steps,
        )


if __name__ == "__main__":
    unittest.main()
