from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
import json
import os
from pathlib import Path
import shlex
import subprocess
from urllib.parse import urlparse

from .adapters import adapter_for
from .config import AppConfig, default_config
from .plan import BrowsePlan, plan_url


ROUTE_AWARE_PROFILE = "route-aware"
ROUTE_AWARE_PAC_NAME = "ampb-proxy.pac"
PAC_URL_PLACEHOLDER = "__AMPB_ROUTE_AWARE_PAC_URL__"


@dataclass(frozen=True)
class BrowserLaunchSpec:
    runtime_path: str
    profile_path: str
    user_js_path: str
    command: tuple[str, ...]
    prefs: tuple[str, ...]
    route_aware: bool = False
    pac_path: str = "-"
    pac_content: str = ""


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


def prepare_open(
    raw_url: str,
    *,
    consent: bool = False,
    dry_run: bool = True,
    config: AppConfig | None = None,
    platform: str | None = None,
    route_aware: bool = False,
) -> OpenPlan:
    config = config or default_config()
    browse_plan = plan_url(raw_url, config=config, platform=platform)
    profile_name = (
        ROUTE_AWARE_PROFILE
        if route_aware and browse_plan.route.transport in {"clearnet", "tor", "i2p"}
        else browse_plan.route.profile
    )
    profile_path = config.profile_path(profile_name)
    proxy = _proxy_for(browse_plan)
    launch_spec = _launch_spec_for(browse_plan, config=config, profile_path=profile_path, route_aware=route_aware)

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
            launch_spec=launch_spec,
        )

    if browse_plan.requires_consent:
        setup_steps = _setup_steps(browse_plan)
        setup_prompt = _setup_prompt(browse_plan, setup_steps, route_aware=route_aware)
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
        launch_spec=launch_spec,
    )


def execute_open(open_plan: OpenPlan, *, root: Path | None = None) -> OpenPlan:
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

    _write_profile(root, spec)
    process = subprocess.Popen(spec.command, cwd=str(root))  # noqa: S603
    return replace(open_plan, dry_run=False, status="launched", browser_pid=process.pid, message="launched bundled browser")


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


def _setup_prompt(browse_plan: BrowsePlan, setup_steps: tuple[str, ...], *, route_aware: bool = False) -> _SetupPrompt:
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
    if route_aware:
        approval_args.append("--route-aware")
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
    route_aware: bool = False,
) -> BrowserLaunchSpec | None:
    if browse_plan.route.transport not in {"clearnet", "tor", "i2p"}:
        return None
    runtime_path = _runtime_path(config)
    user_js_path = str(Path(profile_path) / "user.js")
    command = (runtime_path, "-no-remote", "-profile", profile_path, browse_plan.route.normalized)
    prefs = _prefs_for(browse_plan, route_aware=route_aware)
    pac_path = str(Path(profile_path) / ROUTE_AWARE_PAC_NAME) if route_aware else "-"
    pac_content = _route_aware_pac() if route_aware else ""
    return BrowserLaunchSpec(
        runtime_path=runtime_path,
        profile_path=profile_path,
        user_js_path=user_js_path,
        command=command,
        prefs=prefs,
        route_aware=route_aware,
        pac_path=pac_path,
        pac_content=pac_content,
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


def _prefs_for(browse_plan: BrowsePlan, *, route_aware: bool = False) -> tuple[str, ...]:
    prefs: list[tuple[str, str | int | bool]] = [
        ("browser.shell.checkDefaultBrowser", False),
        ("datareporting.policy.dataSubmissionEnabled", False),
        ("toolkit.telemetry.enabled", False),
        ("network.dns.disablePrefetch", True),
        ("network.predictor.enabled", False),
    ]

    if route_aware:
        prefs.extend(
            [
                ("network.proxy.type", 2),
                ("network.proxy.autoconfig_url", PAC_URL_PLACEHOLDER),
                ("network.proxy.failover_direct", False),
                ("network.proxy.socks_remote_dns", True),
                ("network.proxy.no_proxies_on", ""),
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


def _route_aware_pac() -> str:
    tor_proxy = _pac_proxy_for_endpoint(
        "SOCKS5",
        _endpoint_for_transport("tor", "socks5://127.0.0.1:9050"),
    )
    i2p_proxy = _pac_proxy_for_endpoint(
        "PROXY",
        _endpoint_for_transport("i2p", "http://127.0.0.1:4444"),
    )
    return "\n".join(
        (
            "// Managed by AMPB. Route-aware proxy policy.",
            "function hasSuffix(value, suffix) {",
            "  return value.length >= suffix.length && value.substring(value.length - suffix.length) === suffix;",
            "}",
            "",
            "function FindProxyForURL(url, host) {",
            '  var h = (host || "").toLowerCase();',
            '  if (h.length > 0 && h.charAt(h.length - 1) === ".") {',
            "    h = h.substring(0, h.length - 1);",
            "  }",
            '  if (hasSuffix(h, ".onion")) {',
            f'    return "{tor_proxy}";',
            "  }",
            '  if (hasSuffix(h, ".i2p")) {',
            f'    return "{i2p_proxy}";',
            "  }",
            '  return "DIRECT";',
            "}",
            "",
        )
    )


def _endpoint_for_transport(transport: str, fallback: str) -> str:
    adapter = adapter_for(transport)
    if adapter:
        return adapter.endpoint
    return fallback


def _pac_proxy_for_endpoint(proxy_type: str, endpoint: str) -> str:
    host, port = _endpoint_host_port(endpoint)
    return f"{proxy_type} {host}:{port}"


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


def _write_profile(root: Path, spec: BrowserLaunchSpec) -> None:
    profile_path = _path_from(root, spec.profile_path)
    profile_path.mkdir(parents=True, exist_ok=True)
    pac_url = "-"
    if spec.route_aware and spec.pac_content:
        pac_path = _path_from(root, spec.pac_path)
        pac_path.parent.mkdir(parents=True, exist_ok=True)
        pac_path.write_text(spec.pac_content, encoding="utf-8")
        pac_url = pac_path.resolve().as_uri()
    user_js_path = _path_from(root, spec.user_js_path)
    text = "// Managed by AMPB. Local browser profile policy.\n" + "\n".join(spec.prefs) + "\n"
    text = text.replace(PAC_URL_PLACEHOLDER, pac_url)
    user_js_path.write_text(text, encoding="utf-8")


def _path_from(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path
