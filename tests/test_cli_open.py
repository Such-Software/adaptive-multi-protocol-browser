from __future__ import annotations

from dataclasses import replace
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from ampbrowser.cli import main
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
            with patch("ampbrowser.cli.ensure_transport_ready") as ensure_transport_ready:
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
        )

        def fake_execute(open_plan, *, root: Path):
            return replace(
                open_plan,
                status="launched",
                dry_run=False,
                browser_pid=5678,
                message="launched bundled browser",
            )

        with patch("ampbrowser.plan.inspect_transport", return_value=status):
            with patch("ampbrowser.cli.ensure_transport_ready", return_value=transport_result) as ensure_transport_ready:
                with patch("ampbrowser.cli.execute_open", side_effect=fake_execute) as execute_open:
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
        self.assertIn("transport_setup_owned=true", output)
        self.assertIn("transport_setup_pid=1234", output)
        self.assertIn("transport_setup_endpoint=socks5://127.0.0.1:9050", output)


if __name__ == "__main__":
    unittest.main()
