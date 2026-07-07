from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ampbrowser.config import AppConfig
from ampbrowser.transport_manager import ensure_transport_ready
from ampbrowser.transports import TransportStatus


class TransportManagerTest(unittest.TestCase):
    def test_adopts_running_transport(self) -> None:
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
            result = ensure_transport_ready("tor", config=AppConfig(transport_modes={}), root=Path(tmp), status=status)

        self.assertEqual("ready", result.status)
        self.assertFalse(result.owned)
        self.assertTrue(result.ready)
        self.assertEqual(0, result.pid)

    def test_reports_missing_tor_provider(self) -> None:
        status = TransportStatus(
            transport="tor",
            installed=False,
            running=False,
            endpoint="socks5://127.0.0.1:9050",
            adoptable=False,
            manage_supported=True,
            note="Tor SOCKS proxy",
        )

        with tempfile.TemporaryDirectory() as tmp:
            with patch("ampbrowser.transport_manager.shutil.which", return_value=None):
                result = ensure_transport_ready("tor", config=AppConfig(transport_modes={}), root=Path(tmp), status=status)

        self.assertEqual("missing-provider", result.status)
        self.assertFalse(result.ready)
        self.assertIn("Tor provider not found", result.message)

    def test_starts_configured_tor_provider_with_ampb_state(self) -> None:
        status = TransportStatus(
            transport="tor",
            installed=True,
            running=False,
            endpoint="socks5://127.0.0.1:9050",
            adoptable=False,
            manage_supported=True,
            note="Tor SOCKS proxy",
        )
        config = AppConfig(transport_modes={}, transport_binaries={"tor": "/opt/ampb/tor"})

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("ampbrowser.transport_manager._wait_for_endpoint", return_value=True):
                with patch("ampbrowser.transport_manager.subprocess.Popen") as popen:
                    popen.return_value.pid = 1234
                    result = ensure_transport_ready("tor", config=config, root=root, status=status)

        self.assertEqual("started", result.status)
        self.assertTrue(result.owned)
        self.assertEqual(1234, result.pid)
        self.assertEqual(str(root / ".ampb/transports/tor"), result.state_dir)
        self.assertEqual("/opt/ampb/tor", result.command[0])
        self.assertIn("--DataDirectory", result.command)
        self.assertIn(str(root / ".ampb/transports/tor/data"), result.command)
        popen.assert_called_once()

    def test_reports_tor_spawn_failure(self) -> None:
        status = TransportStatus(
            transport="tor",
            installed=True,
            running=False,
            endpoint="socks5://127.0.0.1:9050",
            adoptable=False,
            manage_supported=True,
            note="Tor SOCKS proxy",
        )
        config = AppConfig(transport_modes={}, transport_binaries={"tor": "/opt/ampb/tor"})

        with tempfile.TemporaryDirectory() as tmp:
            with patch("ampbrowser.transport_manager.subprocess.Popen", side_effect=OSError("nope")):
                result = ensure_transport_ready("tor", config=config, root=Path(tmp), status=status)

        self.assertEqual("start-failed", result.status)
        self.assertFalse(result.ready)
        self.assertIn("could not start", result.message)

    def test_terminates_owned_tor_process_on_timeout(self) -> None:
        status = TransportStatus(
            transport="tor",
            installed=True,
            running=False,
            endpoint="socks5://127.0.0.1:9050",
            adoptable=False,
            manage_supported=True,
            note="Tor SOCKS proxy",
        )
        config = AppConfig(transport_modes={}, transport_binaries={"tor": "/opt/ampb/tor"})

        with tempfile.TemporaryDirectory() as tmp:
            with patch("ampbrowser.transport_manager._wait_for_endpoint", return_value=False):
                with patch("ampbrowser.transport_manager.subprocess.Popen") as popen:
                    popen.return_value.pid = 1234
                    result = ensure_transport_ready("tor", config=config, root=Path(tmp), status=status)

        self.assertEqual("start-timeout", result.status)
        self.assertFalse(result.ready)
        popen.return_value.terminate.assert_called_once()

    def test_non_tor_managed_start_is_reported_as_unsupported(self) -> None:
        status = TransportStatus(
            transport="i2p",
            installed=True,
            running=False,
            endpoint="http://127.0.0.1:4444",
            adoptable=False,
            manage_supported=True,
            note="I2P HTTP proxy",
        )

        with tempfile.TemporaryDirectory() as tmp:
            result = ensure_transport_ready("i2p", config=AppConfig(transport_modes={}), root=Path(tmp), status=status)

        self.assertEqual("unsupported", result.status)
        self.assertFalse(result.ready)
        self.assertIn("not implemented yet", result.message)


if __name__ == "__main__":
    unittest.main()
