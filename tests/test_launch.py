from __future__ import annotations

import unittest
from unittest.mock import patch

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
        self.assertEqual(("install i2p", "start managed i2p", "wait for http://127.0.0.1:4444"), plan.setup_steps)
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
        self.assertEqual(("start managed tor", "wait for socks5://127.0.0.1:9050"), plan.setup_steps)


if __name__ == "__main__":
    unittest.main()
