from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ampbrowser.config import AppConfig
from ampbrowser.transport_manager import ensure_transport_ready, stop_managed_transport, transport_status
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
        self.assertEqual("-", result.provider)
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
                with patch("ampbrowser.transport_manager._bundled_arti_path", return_value=""):
                    result = ensure_transport_ready("tor", config=AppConfig(transport_modes={}), root=Path(tmp), status=status)

        self.assertEqual("missing-provider", result.status)
        self.assertFalse(result.ready)
        self.assertIn("Tor provider not found", result.message)

    def test_starts_bundled_arti_provider_with_ampb_state(self) -> None:
        status = TransportStatus(
            transport="tor",
            installed=True,
            running=False,
            endpoint="socks5://127.0.0.1:9050",
            adoptable=False,
            manage_supported=True,
            note="Tor SOCKS proxy",
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            arti = root / "providers/arti/bin/arti"
            with patch("ampbrowser.transport_manager._wait_for_endpoint", return_value=True):
                with patch("ampbrowser.transport_manager.subprocess.Popen") as popen:
                    with patch("ampbrowser.transport_manager._bundled_arti_path", return_value=str(arti)):
                        popen.return_value.pid = 1234
                        result = ensure_transport_ready("tor", config=AppConfig(transport_modes={}), root=root, status=status)

            self.assertEqual("started", result.status)
            self.assertEqual("arti", result.provider)
            self.assertTrue(result.owned)
            self.assertEqual(1234, result.pid)
            self.assertEqual(str(root / ".ampb/transports/tor"), result.state_dir)
            self.assertEqual(str(arti), result.command[0])
            self.assertIn("proxy", result.command)
            self.assertIn("-p", result.command)
            self.assertIn('storage.state_dir="' + str(root / ".ampb/transports/tor/arti-state") + '"', result.command)
            self.assertIn('storage.cache_dir="' + str(root / ".ampb/transports/tor/arti-cache") + '"', result.command)
            state_path = root / ".ampb/transports/tor/ampb-owned.json"
            self.assertTrue(state_path.exists())
            self.assertIn('"provider": "arti"', state_path.read_text(encoding="utf-8"))
            popen.assert_called_once()

    def test_reuses_recorded_ampb_owned_transport(self) -> None:
        status = TransportStatus(
            transport="tor",
            installed=True,
            running=False,
            endpoint="socks5://127.0.0.1:9050",
            adoptable=False,
            manage_supported=True,
            note="Tor SOCKS proxy",
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / ".ampb/transports/tor"
            state_dir.mkdir(parents=True)
            (state_dir / "ampb-owned.json").write_text(
                """
{
  "command": ["/tmp/arti", "proxy"],
  "endpoint": "socks5://127.0.0.1:9050",
  "pid": 1234,
  "provider": "arti",
  "state_dir": "%s",
  "transport": "tor"
}
""".strip()
                % state_dir,
                encoding="utf-8",
            )
            with patch("ampbrowser.transport_manager._pid_alive", return_value=True):
                with patch("ampbrowser.transport_manager._wait_for_endpoint", return_value=True):
                    with patch("ampbrowser.transport_manager.subprocess.Popen") as popen:
                        result = ensure_transport_ready("tor", config=AppConfig(transport_modes={}), root=root, status=status)

        self.assertEqual("ready", result.status)
        self.assertEqual("arti", result.provider)
        self.assertTrue(result.owned)
        self.assertEqual(1234, result.pid)
        popen.assert_not_called()

    def test_transport_status_removes_stale_owned_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / ".ampb/transports/tor"
            state_dir.mkdir(parents=True)
            state_path = state_dir / "ampb-owned.json"
            state_path.write_text('{"pid": 1234, "provider": "arti", "endpoint": "socks5://127.0.0.1:9050"}\n', encoding="utf-8")
            with patch("ampbrowser.transport_manager._pid_alive", return_value=False):
                result = transport_status("tor", config=AppConfig(transport_modes={}), root=root)

        self.assertEqual("stale", result.status)
        self.assertFalse(state_path.exists())

    def test_transport_status_reports_stale_cleanup_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / ".ampb/transports/tor"
            state_dir.mkdir(parents=True)
            state_path = state_dir / "ampb-owned.json"
            state_path.write_text('{"pid": 1234, "provider": "arti", "endpoint": "socks5://127.0.0.1:9050"}\n', encoding="utf-8")
            with patch("ampbrowser.transport_manager._pid_alive", return_value=False):
                with patch("ampbrowser.transport_manager._unlink_state", return_value=False):
                    result = transport_status("tor", config=AppConfig(transport_modes={}), root=root)

        self.assertEqual("stale-cleanup-failed", result.status)
        self.assertIn("could not remove stale", result.message)

    def test_stop_managed_transport_terminates_recorded_pid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / ".ampb/transports/tor"
            state_dir.mkdir(parents=True)
            state_path = state_dir / "ampb-owned.json"
            state_path.write_text('{"pid": 1234, "provider": "arti", "endpoint": "socks5://127.0.0.1:9050"}\n', encoding="utf-8")

            live = [True]

            def fake_alive(pid: int) -> bool:
                return live[0]

            def fake_kill(pid: int, sig: int) -> None:
                live[0] = False

            with patch("ampbrowser.transport_manager._pid_alive", side_effect=fake_alive):
                with patch("ampbrowser.transport_manager.os.kill", side_effect=fake_kill):
                    result = stop_managed_transport("tor", config=AppConfig(transport_modes={}), root=root)

        self.assertEqual("stopped", result.status)
        self.assertEqual("arti", result.provider)
        self.assertFalse(state_path.exists())

    def test_starts_configured_classic_tor_provider_with_ampb_state(self) -> None:
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
                    with patch("ampbrowser.transport_manager._bundled_arti_path", return_value=""):
                        popen.return_value.pid = 1234
                        result = ensure_transport_ready("tor", config=config, root=root, status=status)

        self.assertEqual("started", result.status)
        self.assertEqual("tor", result.provider)
        self.assertTrue(result.owned)
        self.assertEqual(1234, result.pid)
        self.assertEqual(str(root / ".ampb/transports/tor"), result.state_dir)
        self.assertEqual("/opt/ampb/tor", result.command[0])
        self.assertIn("--DataDirectory", result.command)
        self.assertIn(str(root / ".ampb/transports/tor/tor-data"), result.command)
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
            with patch("ampbrowser.transport_manager._bundled_arti_path", return_value=""):
                with patch("ampbrowser.transport_manager.subprocess.Popen", side_effect=OSError("nope")):
                    result = ensure_transport_ready("tor", config=config, root=Path(tmp), status=status)

        self.assertEqual("start-failed", result.status)
        self.assertEqual("tor", result.provider)
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
                    with patch("ampbrowser.transport_manager._bundled_arti_path", return_value=""):
                        popen.return_value.pid = 1234
                        result = ensure_transport_ready("tor", config=config, root=Path(tmp), status=status)

        self.assertEqual("start-timeout", result.status)
        self.assertFalse(result.ready)
        popen.return_value.terminate.assert_called_once()

    def test_reports_missing_i2p_provider(self) -> None:
        status = TransportStatus(
            transport="i2p",
            installed=False,
            running=False,
            endpoint="http://127.0.0.1:4444",
            adoptable=False,
            manage_supported=True,
            note="I2P HTTP proxy",
        )

        with tempfile.TemporaryDirectory() as tmp:
            with patch("ampbrowser.transport_manager.shutil.which", return_value=None):
                result = ensure_transport_ready("i2p", config=AppConfig(transport_modes={}), root=Path(tmp), status=status)

        self.assertEqual("missing-provider", result.status)
        self.assertFalse(result.ready)
        self.assertIn("I2P provider not found", result.message)
        self.assertIn("brew install i2pd", result.message)

    def test_finds_homebrew_i2pd_provider_when_not_on_path(self) -> None:
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
            root = Path(tmp)
            prefix = root / "homebrew/opt/i2pd"
            i2pd = prefix / "bin/i2pd"
            i2pd.parent.mkdir(parents=True)
            i2pd.write_text("#!/bin/sh\n", encoding="utf-8")

            class Result:
                returncode = 0
                stdout = str(prefix) + "\n"

            def which(name: str) -> str | None:
                return "/opt/homebrew/bin/brew" if name == "brew" else None

            with patch("ampbrowser.transport_manager.shutil.which", side_effect=which):
                with patch("ampbrowser.transport_manager.subprocess.run", return_value=Result()):
                    with patch("ampbrowser.transport_manager._wait_for_endpoint", return_value=True):
                        with patch("ampbrowser.transport_manager.subprocess.Popen") as popen:
                            popen.return_value.pid = 1234
                            result = ensure_transport_ready("i2p", config=AppConfig(transport_modes={}), root=root, status=status)

        self.assertEqual("started", result.status)
        self.assertEqual(str(i2pd), result.command[0])

    def test_starts_configured_i2pd_provider_with_ampb_state(self) -> None:
        status = TransportStatus(
            transport="i2p",
            installed=True,
            running=False,
            endpoint="http://127.0.0.1:4444",
            adoptable=False,
            manage_supported=True,
            note="I2P HTTP proxy",
        )
        config = AppConfig(transport_modes={}, transport_binaries={"i2p": "/opt/ampb/i2pd"})

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("ampbrowser.transport_manager._wait_for_endpoint", return_value=True):
                with patch("ampbrowser.transport_manager.subprocess.Popen") as popen:
                    popen.return_value.pid = 1234
                    result = ensure_transport_ready("i2p", config=config, root=root, status=status)

            self.assertEqual("started", result.status)
            self.assertEqual("i2pd", result.provider)
            self.assertTrue(result.owned)
            self.assertEqual(1234, result.pid)
            self.assertEqual(str(root / ".ampb/transports/i2p"), result.state_dir)
            self.assertEqual("/opt/ampb/i2pd", result.command[0])
            self.assertIn("--conf", result.command)
            self.assertIn(str(root / ".ampb/transports/i2p/i2pd.conf"), result.command)
            self.assertIn("--datadir", result.command)
            self.assertIn(str(root / ".ampb/transports/i2p/i2pd-data"), result.command)
            config_text = (root / ".ampb/transports/i2p/i2pd.conf").read_text(encoding="utf-8")
            self.assertIn("[httpproxy]", config_text)
            self.assertIn("address = 127.0.0.1", config_text)
            self.assertIn("port = 4444", config_text)
            self.assertIn("daemon = false", config_text)
            self.assertIn("service = false", config_text)
            self.assertIn("notransit = true", config_text)
            state_path = root / ".ampb/transports/i2p/ampb-owned.json"
            self.assertTrue(state_path.exists())
            self.assertIn('"provider": "i2pd"', state_path.read_text(encoding="utf-8"))
            popen.assert_called_once()

    def test_terminates_owned_i2pd_process_on_timeout(self) -> None:
        status = TransportStatus(
            transport="i2p",
            installed=True,
            running=False,
            endpoint="http://127.0.0.1:4444",
            adoptable=False,
            manage_supported=True,
            note="I2P HTTP proxy",
        )
        config = AppConfig(transport_modes={}, transport_binaries={"i2p": "/opt/ampb/i2pd"})

        with tempfile.TemporaryDirectory() as tmp:
            with patch("ampbrowser.transport_manager._wait_for_endpoint", return_value=False):
                with patch("ampbrowser.transport_manager.subprocess.Popen") as popen:
                    popen.return_value.pid = 1234
                    result = ensure_transport_ready("i2p", config=config, root=Path(tmp), status=status)

        self.assertEqual("start-timeout", result.status)
        self.assertFalse(result.ready)
        popen.return_value.terminate.assert_called_once()

    def test_other_managed_start_is_reported_as_unsupported(self) -> None:
        status = TransportStatus(
            transport="ipfs",
            installed=True,
            running=False,
            endpoint="http://127.0.0.1:8080",
            adoptable=False,
            manage_supported=True,
            note="IPFS local gateway",
        )

        with tempfile.TemporaryDirectory() as tmp:
            result = ensure_transport_ready("ipfs", config=AppConfig(transport_modes={}), root=Path(tmp), status=status)

        self.assertEqual("unsupported", result.status)
        self.assertFalse(result.ready)
        self.assertIn("not implemented yet", result.message)


if __name__ == "__main__":
    unittest.main()
