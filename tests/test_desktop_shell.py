from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ampbrowser.config import AppConfig
from ampbrowser.desktop_shell import launch_desktop_shell
from ampbrowser.transports import TransportStatus


class DesktopShellTest(unittest.TestCase):
    def test_shell_cancel_does_not_launch(self) -> None:
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
            with patch("ampbrowser.plan.inspect_transport", return_value=status):
                with patch("ampbrowser.desktop_shell.launch_open_plan") as launch:
                    result = launch_desktop_shell(
                        "http://example.onion/",
                        config=AppConfig(transport_modes={}),
                        root=Path(tmp),
                        prompt_driver=lambda open_plan: False,
                    )

        self.assertEqual("cancelled", result.open_plan.status)
        self.assertTrue(result.prompt_shown)
        self.assertFalse(result.prompt_approved)
        launch.assert_not_called()

    def test_shell_approval_launches_approved_plan(self) -> None:
        status = TransportStatus(
            transport="tor",
            installed=True,
            running=False,
            endpoint="socks5://127.0.0.1:9050",
            adoptable=False,
            manage_supported=True,
            note="Tor SOCKS proxy",
        )

        def fake_launch(open_plan, *, config: AppConfig, root: Path):
            self.assertEqual("setup-approved", open_plan.status)
            return replace(open_plan, status="launched", dry_run=False, browser_pid=1234)

        with tempfile.TemporaryDirectory() as tmp:
            with patch("ampbrowser.plan.inspect_transport", return_value=status):
                with patch("ampbrowser.desktop_shell.launch_open_plan", side_effect=fake_launch) as launch:
                    result = launch_desktop_shell(
                        "http://example.onion/",
                        config=AppConfig(transport_modes={}),
                        root=Path(tmp),
                        prompt_driver=lambda open_plan: True,
                    )

        self.assertEqual("launched", result.open_plan.status)
        self.assertEqual(1234, result.open_plan.browser_pid)
        self.assertTrue(result.prompt_shown)
        self.assertTrue(result.prompt_approved)
        launch.assert_called_once()

    def test_shell_auto_approve_skips_prompt_driver(self) -> None:
        status = TransportStatus(
            transport="tor",
            installed=True,
            running=False,
            endpoint="socks5://127.0.0.1:9050",
            adoptable=False,
            manage_supported=True,
            note="Tor SOCKS proxy",
        )

        def fake_launch(open_plan, *, config: AppConfig, root: Path):
            return replace(open_plan, status="launched", dry_run=False, browser_pid=1234)

        with tempfile.TemporaryDirectory() as tmp:
            with patch("ampbrowser.plan.inspect_transport", return_value=status):
                with patch("ampbrowser.desktop_shell.launch_open_plan", side_effect=fake_launch):
                    result = launch_desktop_shell(
                        "http://example.onion/",
                        config=AppConfig(transport_modes={}),
                        root=Path(tmp),
                        auto_approve=True,
                        prompt_driver=lambda open_plan: False,
                    )

        self.assertEqual("launched", result.open_plan.status)
        self.assertFalse(result.prompt_shown)
        self.assertTrue(result.prompt_approved)


if __name__ == "__main__":
    unittest.main()
