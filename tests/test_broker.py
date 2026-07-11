from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ampbrowser.broker import BrokerRouteError, open_brokered_url
from ampbrowser.config import AppConfig
from ampbrowser.transports import TransportStatus


class BrokerTest(unittest.TestCase):
    def test_broker_launches_matching_route_without_shared_profile(self) -> None:
        status = TransportStatus(
            transport="tor",
            installed=True,
            running=True,
            endpoint="socks5://127.0.0.1:9050",
            adoptable=True,
            manage_supported=True,
            note="Tor SOCKS proxy",
        )

        with tempfile.TemporaryDirectory() as tmp:
            with patch("ampbrowser.plan.inspect_transport", return_value=status):
                with patch("ampbrowser.broker.launch_open_plan", side_effect=lambda plan, **_: plan) as launch:
                    result = open_brokered_url(
                        "http://example.onion/",
                        expected_transport="tor",
                        consent=False,
                        config=AppConfig(transport_modes={}),
                        root=Path(tmp),
                    )

        self.assertEqual("ready", result.status)
        self.assertEqual(".ampb/profiles/tor", result.profile_path)
        self.assertFalse(result.launch_spec.broker)
        launch.assert_called_once()

    def test_broker_rejects_claimed_transport_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(BrokerRouteError):
                open_brokered_url(
                    "http://example.b32.i2p/",
                    expected_transport="tor",
                    consent=False,
                    config=AppConfig(transport_modes={}),
                    root=Path(tmp),
                )


if __name__ == "__main__":
    unittest.main()
