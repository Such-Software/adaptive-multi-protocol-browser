from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ampbrowser.config import AppConfig
from ampbrowser.launch import prepare_open
from ampbrowser.route_helper import handle_helper_message
from ampbrowser.transport_manager import ManagedTransportResult
from ampbrowser.transports import TransportStatus


class RouteHelperTest(unittest.TestCase):
    def test_status_routes_url_to_transport(self) -> None:
        result = ManagedTransportResult(
            transport="tor",
            provider="arti",
            status="ready",
            endpoint="socks5://127.0.0.1:9050",
            owned=True,
            pid=1234,
            state_dir=".ampb/transports/tor",
            command=("/tmp/arti", "proxy"),
            message="using running AMPB-owned tor",
            provider_source="bundled-sidecar",
        )

        with tempfile.TemporaryDirectory() as tmp:
            with patch("ampbrowser.route_helper.transport_status", return_value=result) as status:
                response = handle_helper_message(
                    {"action": "status", "url": "http://example.onion/"},
                    root=Path(tmp),
                    config=AppConfig(transport_modes={}),
                )

        self.assertTrue(response["ok"])
        self.assertTrue(response["ready"])
        self.assertEqual("tor", response["transport"])
        self.assertEqual("bundled-sidecar", response["provider_source"])
        status.assert_called_once()

    def test_ensure_starts_i2p_transport(self) -> None:
        result = ManagedTransportResult(
            transport="i2p",
            provider="i2pd",
            status="started",
            endpoint="http://127.0.0.1:4444",
            owned=True,
            pid=1234,
            state_dir=".ampb/transports/i2p",
            command=("/opt/i2pd",),
            message="started managed i2pd transport",
            provider_source="system-package",
            setup_hint="Install i2pd with Homebrew: brew install i2pd.",
            install_command=("brew", "install", "i2pd"),
        )

        with tempfile.TemporaryDirectory() as tmp:
            with patch("ampbrowser.route_helper.ensure_transport_ready", return_value=result) as ensure:
                response = handle_helper_message(
                    {"action": "ensure", "transport": "i2p", "url": "http://example.b32.i2p/"},
                    root=Path(tmp),
                    config=AppConfig(transport_modes={}),
                )

        self.assertTrue(response["ok"])
        self.assertTrue(response["ready"])
        self.assertEqual("started", response["status"])
        self.assertEqual("Install i2pd with Homebrew: brew install i2pd.", response["setup_hint"])
        self.assertEqual(["brew", "install", "i2pd"], response["install_command"])
        ensure.assert_called_once()

    def test_blocks_unsupported_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            response = handle_helper_message(
                {"action": "ensure", "url": "https://example.com/"},
                root=Path(tmp),
                config=AppConfig(transport_modes={}),
            )

        self.assertFalse(response["ok"])
        self.assertEqual("unsupported-transport", response["status"])

    def test_open_hands_route_to_isolated_transport_profile(self) -> None:
        status = TransportStatus(
            transport="tor",
            installed=True,
            running=True,
            endpoint="socks5://127.0.0.1:9050",
            adoptable=True,
            manage_supported=True,
            note="Tor SOCKS proxy",
        )
        with patch("ampbrowser.plan.inspect_transport", return_value=status):
            plan = prepare_open("http://example.onion/")
        launched = replace(plan, status="launched", dry_run=False, browser_pid=4321)

        with tempfile.TemporaryDirectory() as tmp:
            with patch("ampbrowser.route_helper.open_brokered_url", return_value=launched) as broker_open:
                response = handle_helper_message(
                    {
                        "action": "open",
                        "transport": "tor",
                        "url": "http://example.onion/",
                        "consent": True,
                    },
                    root=Path(tmp),
                    config=AppConfig(transport_modes={}),
                )

        self.assertTrue(response["ok"])
        self.assertTrue(response["launched"])
        self.assertEqual("tor", response["profile"])
        self.assertEqual(".ampb/profiles/tor", response["profile_path"])
        self.assertEqual(4321, response["browser_pid"])
        broker_open.assert_called_once()

    def test_open_rejects_transport_url_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            response = handle_helper_message(
                {
                    "action": "open",
                    "transport": "tor",
                    "url": "http://example.b32.i2p/",
                },
                root=Path(tmp),
                config=AppConfig(transport_modes={}),
            )

        self.assertFalse(response["ok"])
        self.assertEqual("route-mismatch", response["status"])


if __name__ == "__main__":
    unittest.main()
