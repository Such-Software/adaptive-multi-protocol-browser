from __future__ import annotations

import unittest
from unittest.mock import patch

from ampbrowser.config import AppConfig
from ampbrowser.plan import plan_url
from ampbrowser.transports import TransportStatus


class PlanUrlTest(unittest.TestCase):
    def test_gemini_uses_builtin_transport(self) -> None:
        plan = plan_url("gemini://wownero.org/")

        self.assertEqual("gemini", plan.route.transport)
        self.assertEqual("adopt existing transport", plan.action)
        self.assertIsNotNone(plan.status)
        self.assertTrue(plan.status.adoptable)

    def test_clearnet_opens_with_clearnet_profile(self) -> None:
        plan = plan_url("wownero.org")

        self.assertEqual("https://wownero.org", plan.route.normalized)
        self.assertEqual("clearnet", plan.route.transport)
        self.assertEqual("open with clearnet profile", plan.action)
        self.assertFalse(plan.requires_consent)

    def test_missing_transport_prompts_before_install_or_start(self) -> None:
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
            plan = plan_url("http://example.b32.i2p/")

        self.assertEqual("prompt to install and start managed transport", plan.action)
        self.assertTrue(plan.requires_consent)
        self.assertIn("install and start", plan.prompt)

    def test_stopped_transport_prompts_before_start(self) -> None:
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
            plan = plan_url("http://example.onion/")

        self.assertEqual("prompt to start managed transport", plan.action)
        self.assertTrue(plan.requires_consent)
        self.assertIn("can start", plan.prompt)

    def test_disabled_transport_is_blocked_by_policy(self) -> None:
        config = AppConfig(transport_modes={"i2p": "disabled"})

        plan = plan_url("http://example.b32.i2p/", config=config)

        self.assertEqual("disabled", plan.policy_mode)
        self.assertEqual("blocked by policy: i2p disabled", plan.action)
        self.assertFalse(plan.requires_consent)

    def test_adopt_only_transport_does_not_prompt_to_start(self) -> None:
        status = TransportStatus(
            transport="tor",
            installed=True,
            running=False,
            endpoint="socks5://127.0.0.1:9050",
            adoptable=False,
            manage_supported=True,
            note="Tor SOCKS proxy",
        )
        config = AppConfig(transport_modes={"tor": "adopt"})

        with patch("ampbrowser.plan.inspect_transport", return_value=status):
            plan = plan_url("http://example.onion/", config=config)

        self.assertEqual("adopt", plan.policy_mode)
        self.assertEqual("blocked by policy: tor mode is adopt", plan.action)
        self.assertFalse(plan.requires_consent)

    def test_android_platform_is_reported_on_plan(self) -> None:
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
            plan = plan_url("http://example.onion/", platform="android")

        self.assertEqual("android", plan.platform_capability.platform)
        self.assertEqual("planned", plan.platform_capability.manage)
        self.assertTrue(plan.requires_consent)

    def test_ipfs_missing_gateway_prompts_before_setup(self) -> None:
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
            plan = plan_url("ipfs://bafyexample")

        self.assertEqual("ipfs", plan.route.transport)
        self.assertEqual("prompt to install and start managed transport", plan.action)
        self.assertTrue(plan.requires_consent)

    def test_ios_foreground_only_transport_prompt(self) -> None:
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
            plan = plan_url("http://example.onion/", platform="ios")

        self.assertEqual("prompt to enable foreground-only transport session", plan.action)
        self.assertIn("foreground-only", plan.prompt)


if __name__ == "__main__":
    unittest.main()
