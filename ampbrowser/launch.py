from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
import json
import os
from pathlib import Path
import secrets
import signal
import shlex
import socket
import subprocess
import sys
import time
from urllib.parse import urlparse

from .adapters import adapter_for
from .config import AppConfig, default_config
from .plan import BrowsePlan, plan_url


BROKER_PROFILE = "broker"
ROUTE_HELPER_EXTENSION_ID = "ampb-route-helper@such.software"
HELPER_URL_PLACEHOLDER = "__AMPB_ROUTE_HELPER_URL__"
HELPER_TOKEN_PLACEHOLDER = "__AMPB_ROUTE_HELPER_TOKEN__"
PROFILE_SESSION_NAME = "ampb-session.json"


@dataclass(frozen=True)
class ProfileAsset:
    path: str
    content: str


@dataclass(frozen=True)
class RouteHelperLaunch:
    status: str
    endpoint: str = "-"
    token: str = "-"
    pid: int = 0
    watch_pid: int = 0
    command: tuple[str, ...] = ()
    message: str = "-"


@dataclass(frozen=True)
class BrowserLaunchSpec:
    runtime_path: str
    profile_path: str
    user_js_path: str
    command: tuple[str, ...]
    prefs: tuple[str, ...]
    broker: bool = False
    extension_path: str = "-"
    extension_assets: tuple[ProfileAsset, ...] = ()


@dataclass(frozen=True)
class OpenPlan:
    browse_plan: BrowsePlan
    status: str
    dry_run: bool
    consent_granted: bool
    profile_path: str
    proxy: str
    setup_steps: tuple[str, ...]
    message: str
    broker: bool = False
    launch_spec: BrowserLaunchSpec | None = None
    browser_pid: int = 0
    setup_prompt_title: str = "-"
    setup_prompt_body: str = "-"
    setup_prompt_approve_label: str = "-"
    setup_prompt_approval_command: str = "-"
    transport_setup_status: str = "-"
    transport_setup_provider: str = "-"
    transport_setup_provider_source: str = "-"
    transport_setup_owned: bool = False
    transport_setup_pid: int = 0
    transport_setup_endpoint: str = "-"
    transport_setup_message: str = "-"
    route_helper_status: str = "-"
    route_helper_endpoint: str = "-"
    route_helper_pid: int = 0
    route_helper_message: str = "-"


def prepare_open(
    raw_url: str,
    *,
    consent: bool = False,
    dry_run: bool = True,
    config: AppConfig | None = None,
    platform: str | None = None,
    broker: bool = False,
    route_aware: bool = False,
) -> OpenPlan:
    config = config or default_config()
    browse_plan = plan_url(raw_url, config=config, platform=platform)
    broker = broker or route_aware
    if broker and browse_plan.route.transport != "clearnet":
        return OpenPlan(
            browse_plan=browse_plan,
            status="blocked",
            dry_run=dry_run,
            consent_granted=consent,
            profile_path=config.profile_path(BROKER_PROFILE),
            proxy="-",
            setup_steps=(),
            message="broker entry URLs must use clearnet; alternate routes open in their isolated profile",
            broker=True,
        )
    profile_name = (
        BROKER_PROFILE
        if broker
        else browse_plan.route.profile
    )
    profile_path = config.profile_path(profile_name)
    proxy = _proxy_for(browse_plan)
    launch_spec = _launch_spec_for(browse_plan, config=config, profile_path=profile_path, broker=broker)

    if browse_plan.action.startswith("blocked"):
        return OpenPlan(
            browse_plan=browse_plan,
            status="blocked",
            dry_run=dry_run,
            consent_granted=consent,
            profile_path=profile_path,
            proxy=proxy,
            setup_steps=(),
            message=browse_plan.action,
            broker=broker,
            launch_spec=launch_spec,
        )

    if browse_plan.requires_consent:
        setup_steps = _setup_steps(browse_plan)
        setup_prompt = _setup_prompt(browse_plan, setup_steps)
        if not consent:
            return OpenPlan(
                browse_plan=browse_plan,
                status="consent-required",
                dry_run=dry_run,
                consent_granted=False,
                profile_path=profile_path,
                proxy=proxy,
                setup_steps=setup_steps,
                message=browse_plan.prompt,
                broker=broker,
                launch_spec=launch_spec,
                setup_prompt_title=setup_prompt.title,
                setup_prompt_body=setup_prompt.body,
                setup_prompt_approve_label=setup_prompt.approve_label,
                setup_prompt_approval_command=setup_prompt.approval_command,
            )
        return OpenPlan(
            browse_plan=browse_plan,
            status="setup-approved",
            dry_run=dry_run,
            consent_granted=True,
            profile_path=profile_path,
            proxy=proxy,
            setup_steps=setup_steps,
            message="first-use setup approved; browser launch waits for transport readiness",
            broker=broker,
            launch_spec=launch_spec,
            setup_prompt_title=setup_prompt.title,
            setup_prompt_body=setup_prompt.body,
            setup_prompt_approve_label=setup_prompt.approve_label,
            setup_prompt_approval_command=setup_prompt.approval_command,
        )

    return OpenPlan(
        browse_plan=browse_plan,
        status="ready",
        dry_run=dry_run,
        consent_granted=consent,
        profile_path=profile_path,
        proxy=proxy,
        setup_steps=(),
        message="ready to open with isolated profile",
        broker=broker,
        launch_spec=launch_spec,
    )


def execute_open(
    open_plan: OpenPlan,
    *,
    root: Path | None = None,
    config: AppConfig | None = None,
) -> OpenPlan:
    root = root or Path.cwd()
    spec = open_plan.launch_spec
    if spec is None:
        return replace(
            open_plan,
            dry_run=False,
            status="launch-unsupported",
            message=f"no browser launch path for {open_plan.browse_plan.route.transport}",
        )
    if open_plan.status != "ready":
        return replace(
            open_plan,
            dry_run=False,
            message=f"not launched: {open_plan.message}",
        )

    runtime_path = _path_from(root, spec.runtime_path)
    if not runtime_path.exists():
        return replace(
            open_plan,
            dry_run=False,
            status="runtime-missing",
            message=f"browser runtime not found: {spec.runtime_path}",
        )

    active_pid = _active_profile_session(root, spec)
    if active_pid:
        return _open_existing_profile(open_plan, root=root, spec=spec, active_pid=active_pid)

    config_path = Path(config.config_path) if config and config.config_path else None
    route_helper = (
        _route_helper_launch_plan(root, config_path=config_path)
        if spec.broker
        else RouteHelperLaunch("disabled")
    )
    _write_profile(root, spec, route_helper=route_helper)
    launch_spec = replace(spec, command=_execution_command(root, spec))
    process = subprocess.Popen(launch_spec.command, cwd=str(root), start_new_session=True)  # noqa: S603
    if spec.broker:
        route_helper = _start_route_helper(
            root,
            planned=route_helper,
            watch_pid=process.pid,
            config_path=config_path,
        )
    exit_code = _immediate_exit_code(process)
    if exit_code is not None:
        helper_status = route_helper.status
        helper_message = route_helper.message
        if spec.broker:
            helper_status = _stop_route_helper(route_helper)
            helper_message = "stopped route helper after browser exited immediately"
        return replace(
            open_plan,
            dry_run=False,
            launch_spec=launch_spec,
            status="browser-exited",
            browser_pid=process.pid,
            message=f"browser exited immediately with code {exit_code}",
            route_helper_status=helper_status,
            route_helper_endpoint=route_helper.endpoint,
            route_helper_pid=route_helper.pid,
            route_helper_message=helper_message,
        )
    _record_profile_session(root, spec, process.pid)
    message = "launched bundled browser"
    if spec.broker:
        message = f"launched isolated transport broker with route helper {route_helper.status}"
    return replace(
        open_plan,
        dry_run=False,
        launch_spec=launch_spec,
        status="launched",
        browser_pid=process.pid,
        message=message,
        route_helper_status=route_helper.status,
        route_helper_endpoint=route_helper.endpoint,
        route_helper_pid=route_helper.pid,
        route_helper_message=route_helper.message,
    )


def _proxy_for(browse_plan: BrowsePlan) -> str:
    if browse_plan.route.transport in {"tor", "i2p"} and browse_plan.status:
        return browse_plan.status.endpoint
    return "-"


def _setup_steps(browse_plan: BrowsePlan) -> tuple[str, ...]:
    if not browse_plan.status:
        return ()
    adapter = adapter_for(browse_plan.route.transport)
    if not adapter:
        return ()

    steps: list[str] = []
    platform = browse_plan.platform_capability.platform
    if platform == "android" and not browse_plan.status.installed:
        steps.append(f"install or enable Android {browse_plan.route.transport} provider")
        steps.extend(adapter.setup_steps(installed=True, platform=platform))
        return tuple(steps)
    if platform == "ios" and not browse_plan.status.installed:
        if browse_plan.route.transport == "tor":
            steps.append("enable bundled iOS Arti Tor runtime")
        else:
            steps.append(f"enable foreground iOS {browse_plan.route.transport} session")
        steps.extend(adapter.setup_steps(installed=True, platform=platform))
        return tuple(steps)
    steps.extend(adapter.setup_steps(installed=browse_plan.status.installed, platform=platform))
    return tuple(steps)


@dataclass(frozen=True)
class _SetupPrompt:
    title: str
    body: str
    approve_label: str
    approval_command: str


def _setup_prompt(browse_plan: BrowsePlan, setup_steps: tuple[str, ...]) -> _SetupPrompt:
    transport = browse_plan.route.transport
    label = _transport_label(transport)
    platform = browse_plan.platform_capability.platform
    endpoint = browse_plan.status.endpoint if browse_plan.status else "-"
    setup_summary = "; ".join(setup_steps) if setup_steps else "prepare the transport"
    if browse_plan.status and not browse_plan.status.installed:
        availability = f"{label} is not installed or running."
    else:
        availability = f"{label} is not running."
    if platform == "desktop":
        management = f"AMPB can start a managed {label} session and keep its state isolated."
    elif platform == "android":
        management = f"AMPB can start a visible Android foreground {label} session."
    elif platform == "ios":
        management = f"AMPB can start a foreground-only in-app {label} session."
    else:
        management = f"AMPB can prepare {label} for this platform."
    body = (
        f"{availability} {management} The browser will use {endpoint} for "
        f"{browse_plan.route.normalized}. Setup plan: {setup_summary}."
    )
    approval_args = ["ampbrowser", "open", browse_plan.route.normalized, "--yes", "--launch"]
    approval_command = shlex.join(approval_args)
    return _SetupPrompt(
        title=f"Set up {label}?",
        body=body,
        approve_label=f"Start {label} and open",
        approval_command=approval_command,
    )


def _transport_label(transport: str) -> str:
    labels = {
        "tor": "Tor",
        "i2p": "I2P",
        "ipfs": "IPFS",
        "gemini": "Gemini",
        "reticulum": "Reticulum",
    }
    return labels.get(transport, transport)


def _launch_spec_for(
    browse_plan: BrowsePlan,
    *,
    config: AppConfig,
    profile_path: str,
    broker: bool = False,
) -> BrowserLaunchSpec | None:
    if browse_plan.route.transport not in {"clearnet", "tor", "i2p"}:
        return None
    runtime_path = _runtime_path(config)
    user_js_path = str(Path(profile_path) / "user.js")
    command = (runtime_path, "--new-instance", "--profile", profile_path, browse_plan.route.normalized)
    prefs = _prefs_for(browse_plan, broker=broker)
    extension_path = str(Path(profile_path) / "extensions" / ROUTE_HELPER_EXTENSION_ID) if broker else "-"
    extension_assets = _route_helper_extension_assets(extension_path) if broker else ()
    return BrowserLaunchSpec(
        runtime_path=runtime_path,
        profile_path=profile_path,
        user_js_path=user_js_path,
        command=command,
        prefs=prefs,
        broker=broker,
        extension_path=extension_path,
        extension_assets=extension_assets,
    )


def _runtime_path(config: AppConfig) -> str:
    if config.runtime_path:
        return config.runtime_path
    env_path = os.environ.get("AMPB_BROWSER_BIN")
    if env_path:
        return env_path
    build_root = Path(os.environ.get("AMPB_BROWSER_BUILD_ROOT", "/tmp/ampb-browser-build"))
    for candidate in _runtime_candidates(build_root):
        if candidate.exists():
            return str(candidate)
    return str(_runtime_candidates(build_root)[0])


def _runtime_candidates(build_root: Path) -> tuple[Path, ...]:
    return (
        build_root / "obj/gecko-desktop-source/dist/Nightly.app/Contents/MacOS/firefox",
        build_root / "obj/gecko-desktop-source/dist/bin/firefox",
        build_root / "obj/gecko-desktop-artifact/dist/Nightly.app/Contents/MacOS/firefox",
        build_root / "obj/gecko-desktop-artifact/dist/bin/firefox",
    )


def _prefs_for(browse_plan: BrowsePlan, *, broker: bool = False) -> tuple[str, ...]:
    prefs: list[tuple[str, str | int | bool]] = [
        ("browser.shell.checkDefaultBrowser", False),
        ("datareporting.policy.dataSubmissionEnabled", False),
        ("toolkit.telemetry.enabled", False),
        ("network.dns.disablePrefetch", True),
        ("network.predictor.enabled", False),
    ]

    if broker:
        prefs.extend(
            [
                ("network.proxy.type", 0),
                ("extensions.autoDisableScopes", 0),
                ("extensions.enabledScopes", 5),
                ("xpinstall.signatures.required", False),
            ]
        )
        return tuple(_format_pref(name, value) for name, value in prefs)

    transport = browse_plan.route.transport
    if transport == "tor" and browse_plan.status:
        host, port = _endpoint_host_port(browse_plan.status.endpoint)
        prefs.extend(
            [
                ("network.proxy.type", 1),
                ("network.proxy.socks", host),
                ("network.proxy.socks_port", port),
                ("network.proxy.socks_version", 5),
                ("network.proxy.socks_remote_dns", True),
                ("network.proxy.no_proxies_on", ""),
            ]
        )
    elif transport == "i2p" and browse_plan.status:
        host, port = _endpoint_host_port(browse_plan.status.endpoint)
        prefs.extend(
            [
                ("network.proxy.type", 1),
                ("network.proxy.http", host),
                ("network.proxy.http_port", port),
                ("network.proxy.ssl", host),
                ("network.proxy.ssl_port", port),
                ("network.proxy.no_proxies_on", ""),
            ]
        )
    else:
        prefs.append(("network.proxy.type", 0))

    return tuple(_format_pref(name, value) for name, value in prefs)


def _route_helper_extension_assets(extension_path: str) -> tuple[ProfileAsset, ...]:
    base = Path(extension_path)
    return (
        ProfileAsset(str(base / "manifest.json"), _route_helper_manifest()),
        ProfileAsset(str(base / "background.js"), _route_helper_background_js()),
        ProfileAsset(str(base / "setup.html"), _route_helper_setup_html()),
        ProfileAsset(str(base / "setup.js"), _route_helper_setup_js()),
        ProfileAsset(str(base / "setup.css"), _route_helper_setup_css()),
        ProfileAsset(str(base / "handoff.html"), _route_helper_handoff_html()),
        ProfileAsset(str(base / "handoff.js"), _route_helper_handoff_js()),
    )


def _route_helper_manifest() -> str:
    return json.dumps(
        {
            "manifest_version": 2,
            "name": "AMPB Route Helper",
            "version": "0.1.0",
            "description": "Hands alternate-network links to isolated AMPB transport profiles.",
            "applications": {"gecko": {"id": ROUTE_HELPER_EXTENSION_ID}},
            "permissions": [
                "tabs",
                "webRequest",
                "webRequestBlocking",
                "http://*.onion/*",
                "https://*.onion/*",
                "ws://*.onion/*",
                "wss://*.onion/*",
                "http://*.i2p/*",
                "https://*.i2p/*",
                "ws://*.i2p/*",
                "wss://*.i2p/*",
                "http://127.0.0.1/*",
            ],
            "background": {"scripts": ["background.js"]},
        },
        indent=2,
        sort_keys=True,
    ) + "\n"


def _route_helper_background_js() -> str:
    return "\n".join(
        (
            '"use strict";',
            "",
            f'const HELPER_URL = "{HELPER_URL_PLACEHOLDER}";',
            f'const HELPER_TOKEN = "{HELPER_TOKEN_PLACEHOLDER}";',
            "const pendingByTab = new Map();",
            "",
            "function transportForUrl(rawUrl) {",
            "  try {",
            "    const parsed = new URL(rawUrl);",
            "    const host = parsed.hostname.toLowerCase().replace(/\\.$/, '');",
            "    if (host.endsWith('.onion')) return 'tor';",
            "    if (host.endsWith('.i2p')) return 'i2p';",
            "  } catch (_error) {}",
            "  return '';",
            "}",
            "",
            "async function helper(action, transport, url, consent = false) {",
            "  const response = await fetch(HELPER_URL, {",
            "    method: 'POST',",
            "    headers: {",
            "      'Content-Type': 'application/json',",
            "      'X-AMPB-Token': HELPER_TOKEN,",
            "    },",
            "    body: JSON.stringify({ action, transport, url, consent }),",
            "  });",
            "  return response.json();",
            "}",
            "",
            "function internalUrl(page, transport, url, result) {",
            "  const installCommand = Array.isArray(result.install_command) ? result.install_command.join(' ') : '';",
            "  const params = new URLSearchParams({",
            "    transport,",
            "    url,",
            "    message: result.message || '',",
            "    hint: result.setup_hint || '',",
            "    install: installCommand,",
            "  });",
            "  return browser.runtime.getURL(`${page}.html?${params.toString()}`);",
            "}",
            "",
            "async function handoff(details, transport) {",
            "  let result;",
            "  try {",
            "    result = await helper('open', transport, details.url, false);",
            "  } catch (error) {",
            "    result = { ok: false, launched: false, message: String(error) };",
            "  }",
            "  const page = result.launched ? 'handoff' : 'setup';",
            "  try {",
            "    await browser.tabs.update(details.tabId, { url: internalUrl(page, transport, details.url, result) });",
            "  } finally {",
            "    pendingByTab.delete(details.tabId);",
            "  }",
            "}",
            "",
            "function interceptRequest(details) {",
            "  const transport = transportForUrl(details.url);",
            "  if (!transport) return {};",
            "  if (details.type !== 'main_frame' || details.tabId < 0) return { cancel: true };",
            "  if (pendingByTab.get(details.tabId) === details.url) return { cancel: true };",
            "  pendingByTab.set(details.tabId, details.url);",
            "  void handoff(details, transport);",
            "  return { cancel: true };",
            "}",
            "",
            "browser.webRequest.onBeforeRequest.addListener(",
            "  interceptRequest,",
            "  { urls: ['http://*.onion/*', 'https://*.onion/*', 'ws://*.onion/*', 'wss://*.onion/*', 'http://*.i2p/*', 'https://*.i2p/*', 'ws://*.i2p/*', 'wss://*.i2p/*'] },",
            "  ['blocking']",
            ");",
            "",
            "browser.runtime.onMessage.addListener((message) => {",
            "  if (!message || message.type !== 'ampb-open') return false;",
            "  return helper('open', message.transport, message.url, message.consent === true);",
            "});",
            "",
        )
    )


def _route_helper_setup_html() -> str:
    return "\n".join(
        (
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            "  <title>Set Up Transport</title>",
            '  <link rel="stylesheet" href="setup.css">',
            "</head>",
            "<body>",
            '  <main class="panel">',
            '    <p class="eyebrow">AMPB Route Helper</p>',
            '    <h1 id="title">Set Up Transport</h1>',
            '    <p id="body">AMPB needs to start a local transport before opening this route.</p>',
            '    <pre id="url"></pre>',
            '    <p id="message" class="message"></p>',
            '    <pre id="install-command" class="install-command" hidden></pre>',
            '    <button id="approve" type="button">Start and open</button>',
            '    <p id="status" class="status"></p>',
            "  </main>",
            '  <script src="setup.js"></script>',
            "</body>",
            "</html>",
            "",
        )
    )


def _route_helper_setup_js() -> str:
    return "\n".join(
        (
            '"use strict";',
            "",
            "const params = new URLSearchParams(window.location.search);",
            "const transport = params.get('transport') || '';",
            "const url = params.get('url') || '';",
            "const message = params.get('message') || '';",
            "const hint = params.get('hint') || '';",
            "const install = params.get('install') || '';",
            "const label = transport === 'tor' ? 'Tor' : transport === 'i2p' ? 'I2P' : transport;",
            "",
            "function showInstallCommand(value) {",
            "  const installCommand = document.getElementById('install-command');",
            "  if (!value) {",
            "    installCommand.hidden = true;",
            "    installCommand.textContent = '';",
            "    return;",
            "  }",
            "  installCommand.hidden = false;",
            "  installCommand.textContent = value;",
            "}",
            "",
            "document.getElementById('title').textContent = `Set up ${label}?`;",
            "document.getElementById('body').textContent = `AMPB can start a managed ${label} session and keep its state isolated.`;",
            "document.getElementById('url').textContent = url;",
            "document.getElementById('message').textContent = hint || message;",
            "document.getElementById('approve').textContent = `Start ${label} and open`;",
            "showInstallCommand(install);",
            "",
            "document.getElementById('approve').addEventListener('click', async () => {",
            "  const status = document.getElementById('status');",
            "  status.textContent = `Starting ${label}...`;",
            "  const result = await browser.runtime.sendMessage({ type: 'ampb-open', transport, url, consent: true });",
            "  if (result && result.launched) {",
            "    status.textContent = `${label} opened in its isolated browser profile.`;",
            "    const params = new URLSearchParams({ transport, url });",
            "    window.location.href = browser.runtime.getURL(`handoff.html?${params.toString()}`);",
            "    return;",
            "  }",
            "  if (result && Array.isArray(result.install_command)) {",
            "    showInstallCommand(result.install_command.join(' '));",
            "  }",
            "  status.textContent = (result && result.message) || `${label} did not become ready.`;",
            "});",
            "",
        )
    )


def _route_helper_setup_css() -> str:
    return "\n".join(
        (
            ":root { color-scheme: light dark; font-family: system-ui, sans-serif; }",
            "body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: #111; color: #f7f1e8; }",
            ".panel { width: min(680px, calc(100vw - 32px)); }",
            ".eyebrow { color: #36d1c4; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }",
            "h1 { font-size: 2rem; margin: 0 0 12px; }",
            "pre { white-space: pre-wrap; overflow-wrap: anywhere; padding: 12px; border: 1px solid #444; }",
            ".install-command { background: #1d1d1d; border-color: #36d1c4; color: #f7f1e8; }",
            "button { font: inherit; font-weight: 700; padding: 12px 16px; border: 0; background: #36d1c4; color: #111; }",
            ".message, .status { color: #cfc7bb; }",
            "",
        )
    )


def _route_helper_handoff_html() -> str:
    return "\n".join(
        (
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            "  <title>Route Opened</title>",
            '  <link rel="stylesheet" href="setup.css">',
            "</head>",
            "<body>",
            '  <main class="panel">',
            '    <p class="eyebrow">AMPB Transport Broker</p>',
            '    <h1 id="title">Route opened</h1>',
            '    <p id="body">The destination is open in its isolated transport profile.</p>',
            '    <pre id="url"></pre>',
            "  </main>",
            '  <script src="handoff.js"></script>',
            "</body>",
            "</html>",
            "",
        )
    )


def _route_helper_handoff_js() -> str:
    return "\n".join(
        (
            '"use strict";',
            "",
            "const params = new URLSearchParams(window.location.search);",
            "const transport = params.get('transport') || '';",
            "const url = params.get('url') || '';",
            "const label = transport === 'tor' ? 'Tor' : transport === 'i2p' ? 'I2P' : transport;",
            "document.getElementById('title').textContent = `${label} route opened`;",
            "document.getElementById('body').textContent = `This destination opened in the isolated ${label} profile. This clearnet profile did not load it.`;",
            "document.getElementById('url').textContent = url;",
            "",
        )
    )


def _endpoint_host_port(endpoint: str) -> tuple[str, int]:
    parsed = urlparse(endpoint)
    return parsed.hostname or "127.0.0.1", parsed.port or 0


def _format_pref(name: str, value: str | int | bool) -> str:
    if isinstance(value, bool):
        literal = "true" if value else "false"
    elif isinstance(value, int):
        literal = str(value)
    else:
        literal = json.dumps(value)
    return f"user_pref({json.dumps(name)}, {literal});"


def _route_helper_launch_plan(root: Path, *, config_path: Path | None = None) -> RouteHelperLaunch:
    port = _free_loopback_port()
    token = secrets.token_urlsafe(24)
    endpoint = f"http://127.0.0.1:{port}/"
    return RouteHelperLaunch(
        "planned",
        endpoint=endpoint,
        token=token,
        command=_route_helper_command(root=root, port=port, token=token, config_path=config_path),
    )


def _start_route_helper(
    root: Path,
    *,
    planned: RouteHelperLaunch | None = None,
    watch_pid: int = 0,
    config_path: Path | None = None,
) -> RouteHelperLaunch:
    helper = planned or _route_helper_launch_plan(root, config_path=config_path)
    port = _endpoint_host_port(helper.endpoint)[1]
    command = _route_helper_command(
        root=root,
        port=port,
        token=helper.token,
        watch_pid=watch_pid,
        config_path=config_path,
    )
    try:
        process = subprocess.Popen(command, cwd=str(root), start_new_session=True)  # noqa: S603
    except OSError as exc:
        return replace(helper, status="start-failed", command=command, watch_pid=watch_pid, message=str(exc))
    return replace(helper, status="started", pid=process.pid, watch_pid=watch_pid, command=command, message="-")


def _route_helper_command(
    *,
    root: Path,
    port: int,
    token: str,
    watch_pid: int = 0,
    config_path: Path | None = None,
) -> tuple[str, ...]:
    command = (
        sys.executable,
        "-m",
        "ampbrowser",
        "helper",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--token",
        token,
        "--root",
        str(root),
    )
    if watch_pid > 0:
        command = (*command, "--watch-pid", str(watch_pid))
    if config_path:
        command = (*command, "--config", str(config_path))
    return command


def _execution_command(root: Path, spec: BrowserLaunchSpec) -> tuple[str, ...]:
    command = list(spec.command)
    try:
        profile_index = command.index("--profile") + 1
    except ValueError:
        return tuple(command)
    if profile_index >= len(command):
        return tuple(command)
    command[profile_index] = str(_path_from(root, command[profile_index]))
    return tuple(command)


def _open_existing_profile(
    open_plan: OpenPlan,
    *,
    root: Path,
    spec: BrowserLaunchSpec,
    active_pid: int,
) -> OpenPlan:
    runtime_path = str(_path_from(root, spec.runtime_path))
    profile_path = str(_path_from(root, spec.profile_path))
    command = (runtime_path, "--profile", profile_path, "--new-tab", open_plan.browse_plan.route.normalized)
    try:
        process = subprocess.Popen(command, cwd=str(root), start_new_session=True)  # noqa: S603
    except OSError as exc:
        return replace(
            open_plan,
            dry_run=False,
            status="profile-reuse-failed",
            browser_pid=active_pid,
            message=f"could not open route in active {open_plan.browse_plan.route.profile} profile: {exc}",
        )
    exit_code = _immediate_exit_code(process)
    if exit_code == 0:
        return replace(
            open_plan,
            dry_run=False,
            launch_spec=replace(spec, command=command),
            status="opened-existing",
            browser_pid=active_pid,
            message=f"opened route in active {open_plan.browse_plan.route.profile} profile",
        )
    if exit_code is None:
        _record_profile_session(root, spec, process.pid)
        return replace(
            open_plan,
            dry_run=False,
            launch_spec=replace(spec, command=command),
            status="launched",
            browser_pid=process.pid,
            message=f"launched replacement {open_plan.browse_plan.route.profile} profile process",
        )
    return replace(
        open_plan,
        dry_run=False,
        launch_spec=replace(spec, command=command),
        status="profile-reuse-failed",
        browser_pid=active_pid,
        message=f"active profile rejected route with code {exit_code}",
    )


def _active_profile_session(root: Path, spec: BrowserLaunchSpec) -> int:
    session_path = _profile_session_path(root, spec)
    try:
        data = json.loads(session_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    if not isinstance(data, dict):
        return 0
    pid = data.get("pid")
    runtime_path = data.get("runtime_path")
    if not isinstance(pid, int) or pid <= 0 or runtime_path != str(_path_from(root, spec.runtime_path)):
        return 0
    if _pid_exists(pid):
        return pid
    try:
        session_path.unlink()
    except OSError:
        pass
    return 0


def _record_profile_session(root: Path, spec: BrowserLaunchSpec, pid: int) -> None:
    if not isinstance(pid, int) or pid <= 0:
        return
    session_path = _profile_session_path(root, spec)
    session_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "pid": pid,
        "profile_path": str(_path_from(root, spec.profile_path)),
        "runtime_path": str(_path_from(root, spec.runtime_path)),
    }
    temporary_path = session_path.with_name(f".{PROFILE_SESSION_NAME}.{pid}.tmp")
    try:
        temporary_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary_path.replace(session_path)
    except OSError:
        try:
            temporary_path.unlink()
        except OSError:
            pass


def _profile_session_path(root: Path, spec: BrowserLaunchSpec) -> Path:
    return _path_from(root, spec.profile_path) / PROFILE_SESSION_NAME


def _stop_route_helper(route_helper: RouteHelperLaunch) -> str:
    if route_helper.pid <= 0:
        return route_helper.status
    try:
        os.kill(route_helper.pid, signal.SIGTERM)
    except OSError:
        return "stop-failed"
    return "stopped"


def _immediate_exit_code(process: subprocess.Popen, *, wait_seconds: float = 1.0) -> int | None:
    time.sleep(wait_seconds)
    return_code = process.poll()
    if isinstance(return_code, int):
        return return_code
    return None


def _pid_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _write_profile(root: Path, spec: BrowserLaunchSpec, *, route_helper: RouteHelperLaunch | None = None) -> None:
    profile_path = _path_from(root, spec.profile_path)
    profile_path.mkdir(parents=True, exist_ok=True)
    if spec.broker:
        helper = route_helper or RouteHelperLaunch("disabled")
        for asset in spec.extension_assets:
            asset_path = _path_from(root, asset.path)
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            content = asset.content.replace(HELPER_URL_PLACEHOLDER, helper.endpoint)
            content = content.replace(HELPER_TOKEN_PLACEHOLDER, helper.token)
            asset_path.write_text(content, encoding="utf-8")
    user_js_path = _path_from(root, spec.user_js_path)
    text = "// Managed by AMPB. Local browser profile policy.\n" + "\n".join(spec.prefs) + "\n"
    user_js_path.write_text(text, encoding="utf-8")


def _path_from(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path
