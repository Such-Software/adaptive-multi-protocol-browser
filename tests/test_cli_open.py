from __future__ import annotations

from dataclasses import replace
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from ampbrowser.cli import main
from ampbrowser.config import AppConfig
from ampbrowser.desktop_shell import DesktopShellResult
from ampbrowser.launch import prepare_open
from ampbrowser.transport_manager import ManagedTransportResult
from ampbrowser.transports import TransportStatus


class CliOpenTest(unittest.TestCase):
    def test_onion_launch_without_approval_prints_prompt_without_starting_transport(self) -> None:
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
            with patch("ampbrowser.open_runner.ensure_transport_ready") as ensure_transport_ready:
                with patch.object(sys, "stdout", new_callable=io.StringIO) as stdout:
                    code = main(["open", "http://example.onion/", "--launch"])

        self.assertEqual(0, code)
        ensure_transport_ready.assert_not_called()
        output = stdout.getvalue()
        self.assertIn("status=consent-required", output)
        self.assertIn('setup_prompt_title="Set up Tor?"', output)
        self.assertIn("setup_prompt_approval_command=", output)
        self.assertIn("transport_setup_status=-", output)

    def test_onion_launch_with_approval_starts_transport_before_browser_launch(self) -> None:
        status = TransportStatus(
            transport="tor",
            installed=True,
            running=False,
            endpoint="socks5://127.0.0.1:9050",
            adoptable=False,
            manage_supported=True,
            note="Tor SOCKS proxy",
        )
        transport_result = ManagedTransportResult(
            transport="tor",
            provider="arti",
            status="started",
            endpoint="socks5://127.0.0.1:9050",
            owned=True,
            pid=1234,
            state_dir=".ampb/transports/tor",
            command=("/tmp/arti", "proxy"),
            message="started managed arti transport",
            provider_source="bundled-sidecar",
        )

        def fake_execute(open_plan, *, root: Path, config: AppConfig):
            return replace(
                open_plan,
                status="launched",
                dry_run=False,
                browser_pid=5678,
                message="launched bundled browser",
            )

        with patch("ampbrowser.plan.inspect_transport", return_value=status):
            with patch("ampbrowser.open_runner.ensure_transport_ready", return_value=transport_result) as ensure_transport_ready:
                with patch("ampbrowser.open_runner.execute_open", side_effect=fake_execute) as execute_open:
                    with patch.object(sys, "stdout", new_callable=io.StringIO) as stdout:
                        code = main(["open", "http://example.onion/", "--yes", "--launch"])

        self.assertEqual(0, code)
        ensure_transport_ready.assert_called_once()
        execute_open.assert_called_once()
        output = stdout.getvalue()
        self.assertIn("status=launched", output)
        self.assertIn("browser_pid=5678", output)
        self.assertIn("transport_setup_status=started", output)
        self.assertIn("transport_setup_provider=arti", output)
        self.assertIn("transport_setup_provider_source=bundled-sidecar", output)
        self.assertIn("transport_setup_owned=true", output)
        self.assertIn("transport_setup_pid=1234", output)
        self.assertIn("transport_setup_endpoint=socks5://127.0.0.1:9050", output)

    def test_shell_command_prints_desktop_shell_result(self) -> None:
        config = AppConfig(runtime_path="/opt/ampb/firefox", transport_modes={})
        open_plan = prepare_open("https://wownero.org/", config=config)
        result = DesktopShellResult(open_plan=open_plan, prompt_shown=False, prompt_approved=False)

        with patch("ampbrowser.cli.launch_desktop_shell", return_value=result) as shell:
            with patch.object(sys, "stdout", new_callable=io.StringIO) as stdout:
                code = main(["shell", "https://wownero.org/"])

        self.assertEqual(0, code)
        shell.assert_called_once()
        output = stdout.getvalue()
        self.assertIn("AMPBROWSER_SHELL", output)
        self.assertIn("status=ready", output)
        self.assertIn("prompt_shown=false", output)
        self.assertIn("prompt_approved=false", output)

    def test_broker_open_prints_isolated_broker_profile(self) -> None:
        with patch.object(sys, "stdout", new_callable=io.StringIO) as stdout:
            code = main(["open", "https://ampgateway.site/", "--broker"])

        self.assertEqual(0, code)
        output = stdout.getvalue()
        self.assertIn("broker=true", output)
        self.assertIn("profile_path=.ampb/profiles/broker", output)
        self.assertNotIn("pac_path=", output)

    def test_route_aware_flag_remains_broker_alias(self) -> None:
        with patch.object(sys, "stdout", new_callable=io.StringIO) as stdout:
            code = main(["open", "https://ampgateway.site/", "--route-aware"])

        self.assertEqual(0, code)
        self.assertIn("broker=true", stdout.getvalue())

    def test_hidden_helper_command_passes_watch_pid(self) -> None:
        with patch("ampbrowser.cli.serve_route_helper") as helper:
            code = main(["helper", "--port", "44001", "--token", "test-token", "--watch-pid", "9876"])

        self.assertEqual(0, code)
        helper.assert_called_once()
        self.assertEqual(9876, helper.call_args.kwargs["watch_pid"])

    def test_transport_command_prints_setup_hint(self) -> None:
        result = ManagedTransportResult(
            transport="i2p",
            provider="-",
            status="missing-provider",
            endpoint="http://127.0.0.1:4444",
            owned=False,
            pid=0,
            state_dir=".ampb/transports/i2p",
            command=(),
            message="I2P provider not found.",
            setup_hint="Install i2pd with Homebrew: brew install i2pd.",
            install_command=("brew", "install", "i2pd"),
        )

        with patch("ampbrowser.cli.transport_status", return_value=result):
            with patch.object(sys, "stdout", new_callable=io.StringIO) as stdout:
                code = main(["transport", "status", "i2p"])

        self.assertEqual(0, code)
        output = stdout.getvalue()
        self.assertIn('install_command="brew install i2pd"', output)
        self.assertIn('setup_hint="Install i2pd with Homebrew: brew install i2pd."', output)

    def test_transport_repair_command_prints_result(self) -> None:
        result = ManagedTransportResult(
            transport="tor",
            provider="arti",
            status="repaired",
            endpoint="socks5://127.0.0.1:9050",
            owned=True,
            pid=1234,
            state_dir=".ampb/transports/tor",
            command=("/tmp/arti", "proxy"),
            message="removed AMPB-owned tor runtime state",
            provider_source="bundled-sidecar",
        )

        with patch("ampbrowser.cli.repair_managed_transport", return_value=result) as repair:
            with patch.object(sys, "stdout", new_callable=io.StringIO) as stdout:
                code = main(["transport", "repair", "tor"])

        self.assertEqual(0, code)
        repair.assert_called_once()
        output = stdout.getvalue()
        self.assertIn("status=repaired", output)
        self.assertIn("provider=arti", output)
        self.assertIn('message="removed AMPB-owned tor runtime state"', output)


if __name__ == "__main__":
    unittest.main()
