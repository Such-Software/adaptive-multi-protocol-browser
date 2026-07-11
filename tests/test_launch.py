from __future__ import annotations

import unittest
from unittest.mock import patch
import tempfile
from pathlib import Path

from ampbrowser.config import AppConfig
from ampbrowser.launch import RouteHelperLaunch, execute_open, prepare_open
from ampbrowser.transports import TransportStatus


class PrepareOpenTest(unittest.TestCase):
    def test_clearnet_is_ready_without_consent(self) -> None:
        config = AppConfig(runtime_path="/opt/ampb/firefox", transport_modes={})

        plan = prepare_open("wownero.org", config=config)

        self.assertEqual("ready", plan.status)
        self.assertFalse(plan.browse_plan.requires_consent)
        self.assertEqual(".ampb/profiles/clearnet", plan.profile_path)
        self.assertEqual("-", plan.proxy)
        self.assertIsNotNone(plan.launch_spec)
        self.assertEqual("/opt/ampb/firefox", plan.launch_spec.runtime_path)
        self.assertEqual(".ampb/profiles/clearnet/user.js", plan.launch_spec.user_js_path)
        self.assertEqual(
            ("/opt/ampb/firefox", "--new-instance", "--profile", ".ampb/profiles/clearnet", "https://wownero.org"),
            plan.launch_spec.command,
        )

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
        self.assertEqual("Set up I2P?", plan.setup_prompt_title)
        self.assertIn("I2P is not installed or running.", plan.setup_prompt_body)
        self.assertIn("http://example.b32.i2p/", plan.setup_prompt_body)
        self.assertEqual("Start I2P and open", plan.setup_prompt_approve_label)
        self.assertEqual(
            "ampbrowser open http://example.b32.i2p/ --yes --launch",
            plan.setup_prompt_approval_command,
        )

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
        self.assertEqual("Set up Tor?", plan.setup_prompt_title)
        self.assertIn("Tor is not running.", plan.setup_prompt_body)
        self.assertEqual("Start Tor and open", plan.setup_prompt_approve_label)

    def test_adopted_tor_launch_spec_sets_socks_remote_dns(self) -> None:
        status = TransportStatus(
            transport="tor",
            installed=True,
            running=True,
            endpoint="socks5://127.0.0.1:9050",
            adoptable=True,
            manage_supported=True,
            note="Tor SOCKS proxy",
        )
        config = AppConfig(runtime_path="/opt/ampb/firefox", transport_modes={})

        with patch("ampbrowser.plan.inspect_transport", return_value=status):
            plan = prepare_open("http://example.onion/", config=config)

        self.assertEqual("ready", plan.status)
        self.assertIsNotNone(plan.launch_spec)
        self.assertIn('user_pref("network.proxy.socks", "127.0.0.1");', plan.launch_spec.prefs)
        self.assertIn('user_pref("network.proxy.socks_port", 9050);', plan.launch_spec.prefs)
        self.assertIn('user_pref("network.proxy.socks_remote_dns", true);', plan.launch_spec.prefs)

    def test_execute_open_writes_profile_and_launches_when_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / "firefox"
            runtime.write_text("#!/bin/sh\n", encoding="utf-8")
            config = AppConfig(runtime_path=str(runtime), transport_modes={})
            plan = prepare_open("wownero.org", config=config)

            with patch("ampbrowser.launch.subprocess.Popen") as popen:
                launched = execute_open(plan, root=root)

            self.assertEqual("launched", launched.status)
            self.assertFalse(launched.dry_run)
            self.assertEqual(popen.return_value.pid, launched.browser_pid)
            popen.assert_called_once_with(
                (
                    str(runtime),
                    "--new-instance",
                    "--profile",
                    str(root / ".ampb/profiles/clearnet"),
                    "https://wownero.org",
                ),
                cwd=str(root),
                start_new_session=True,
            )
            user_js = root / ".ampb/profiles/clearnet/user.js"
            self.assertTrue(user_js.exists())
            self.assertIn('user_pref("network.proxy.type", 0);', user_js.read_text(encoding="utf-8"))

    def test_route_aware_open_writes_pac_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / "firefox"
            runtime.write_text("#!/bin/sh\n", encoding="utf-8")
            config = AppConfig(runtime_path=str(runtime), transport_modes={})
            plan = prepare_open("https://ampgateway.site/", config=config, route_aware=True)

            self.assertEqual(".ampb/profiles/route-aware", plan.profile_path)
            self.assertIsNotNone(plan.launch_spec)
            self.assertTrue(plan.launch_spec.route_aware)
            self.assertEqual(".ampb/profiles/route-aware/ampb-proxy.pac", plan.launch_spec.pac_path)
            self.assertIn('user_pref("network.proxy.type", 2);', plan.launch_spec.prefs)
            self.assertIn("__AMPB_ROUTE_AWARE_PAC_URL__", "\n".join(plan.launch_spec.prefs))

            helper = RouteHelperLaunch("started", endpoint="http://127.0.0.1:44001/", token="test-token", pid=4321)
            with patch("ampbrowser.launch._start_route_helper", return_value=helper):
                with patch("ampbrowser.launch.subprocess.Popen") as popen:
                    launched = execute_open(plan, root=root)

            self.assertEqual("launched", launched.status)
            self.assertEqual("started", launched.route_helper_status)
            self.assertEqual("http://127.0.0.1:44001/", launched.route_helper_endpoint)
            self.assertEqual(4321, launched.route_helper_pid)
            popen.assert_called_once_with(
                (
                    str(runtime),
                    "--new-instance",
                    "--profile",
                    str(root / ".ampb/profiles/route-aware"),
                    "https://ampgateway.site/",
                ),
                cwd=str(root),
                start_new_session=True,
            )
            profile = root / ".ampb/profiles/route-aware"
            user_js = (profile / "user.js").read_text(encoding="utf-8")
            pac = (profile / "ampb-proxy.pac").read_text(encoding="utf-8")
            self.assertIn((profile / "ampb-proxy.pac").resolve().as_uri(), user_js)
            self.assertNotIn("__AMPB_ROUTE_AWARE_PAC_URL__", user_js)
            self.assertIn('hasSuffix(h, ".onion")', pac)
            self.assertIn('return "SOCKS5 127.0.0.1:9050";', pac)
            self.assertIn('hasSuffix(h, ".i2p")', pac)
            self.assertIn('return "PROXY 127.0.0.1:4444";', pac)
            self.assertIn('return "DIRECT";', pac)
            extension = profile / "extensions/ampb-route-helper@such.software"
            manifest = (extension / "manifest.json").read_text(encoding="utf-8")
            background = (extension / "background.js").read_text(encoding="utf-8")
            setup = (extension / "setup.html").read_text(encoding="utf-8")
            self.assertIn("webNavigation", manifest)
            self.assertIn("install_command", background)
            self.assertIn("http://127.0.0.1:", background)
            self.assertNotIn("__AMPB_ROUTE_HELPER_URL__", background)
            self.assertNotIn("__AMPB_ROUTE_HELPER_TOKEN__", background)
            self.assertIn("Set Up Transport", setup)
            self.assertIn("install-command", setup)

    def test_execute_open_blocks_when_runtime_is_missing(self) -> None:
        config = AppConfig(runtime_path="/missing/ampb/firefox", transport_modes={})
        plan = prepare_open("wownero.org", config=config)

        launched = execute_open(plan, root=Path("/tmp"))

        self.assertEqual("runtime-missing", launched.status)
        self.assertIn("browser runtime not found", launched.message)

    def test_route_aware_launch_stops_helper_when_browser_exits_immediately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / "firefox"
            runtime.write_text("#!/bin/sh\n", encoding="utf-8")
            config = AppConfig(runtime_path=str(runtime), transport_modes={})
            plan = prepare_open("https://ampgateway.site/", config=config, route_aware=True)
            helper = RouteHelperLaunch("started", endpoint="http://127.0.0.1:44001/", token="test-token", pid=4321)

            with patch("ampbrowser.launch._start_route_helper", return_value=helper):
                with patch("ampbrowser.launch._stop_route_helper", return_value="stopped") as stop_helper:
                    with patch("ampbrowser.launch.subprocess.Popen") as popen:
                        popen.return_value.pid = 9876
                        popen.return_value.poll.return_value = 1
                        launched = execute_open(plan, root=root)

        self.assertEqual("browser-exited", launched.status)
        self.assertEqual(9876, launched.browser_pid)
        self.assertEqual("stopped", launched.route_helper_status)
        self.assertIn("browser exited immediately", launched.message)
        stop_helper.assert_called_once_with(helper)

    def test_route_aware_launch_starts_helper_with_browser_pid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / "firefox"
            runtime.write_text("#!/bin/sh\n", encoding="utf-8")
            config = AppConfig(runtime_path=str(runtime), transport_modes={})
            plan = prepare_open("https://ampgateway.site/", config=config, route_aware=True)
            helper = RouteHelperLaunch("started", endpoint="http://127.0.0.1:44001/", token="test-token", pid=4321)

            with patch("ampbrowser.launch._start_route_helper", return_value=helper) as start_helper:
                with patch("ampbrowser.launch.subprocess.Popen") as popen:
                    popen.return_value.pid = 9876
                    popen.return_value.poll.return_value = None
                    launched = execute_open(plan, root=root)

        self.assertEqual("launched", launched.status)
        start_helper.assert_called_once()
        self.assertEqual(9876, start_helper.call_args.kwargs["watch_pid"])
        self.assertEqual("planned", start_helper.call_args.kwargs["planned"].status)

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
