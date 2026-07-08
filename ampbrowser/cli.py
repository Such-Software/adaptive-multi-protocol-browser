from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import shlex
import sys

from .config import load_config
from .docsgen import generate_docs
from .fixtures import check_fixture_manifest
from .launch import execute_open, prepare_open
from .plan import plan_url
from .platforms import PLATFORM_CHOICES
from .routing import route_url
from .transport_manager import ensure_transport_ready, stop_managed_transport, transport_status
from .transports import inspect_transports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ampbrowser")
    subcommands = parser.add_subparsers(dest="command", required=True)

    route_parser = subcommands.add_parser("route", help="Route a URL to a transport.")
    route_parser.add_argument("url")

    plan_parser = subcommands.add_parser("plan", help="Plan how a URL would be opened.")
    plan_parser.add_argument("url")
    plan_parser.add_argument("--config", type=Path, help="Path to an AMPB config file.")
    plan_parser.add_argument("--platform", choices=PLATFORM_CHOICES, help="Target platform capability profile.")

    open_parser = subcommands.add_parser("open", help="Prepare a transport-aware open plan.")
    open_parser.add_argument("url")
    open_parser.add_argument("--config", type=Path, help="Path to an AMPB config file.")
    open_parser.add_argument("--platform", choices=PLATFORM_CHOICES, help="Target platform capability profile.")
    open_parser.add_argument(
        "--yes",
        action="store_true",
        help="Approve first-use setup in the dry-run plan.",
    )
    open_mode = open_parser.add_mutually_exclusive_group()
    open_mode.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Print the open plan without side effects. This is the current default.",
    )
    open_mode.add_argument(
        "--launch",
        action="store_true",
        help="Create the isolated profile and launch the bundled browser when the route is ready.",
    )

    subcommands.add_parser("inspect", help="Inspect local transport readiness.")

    transport_parser = subcommands.add_parser("transport", help="Manage AMPB-owned transports.")
    transport_subcommands = transport_parser.add_subparsers(dest="transport_command", required=True)
    transport_status_parser = transport_subcommands.add_parser("status", help="Show AMPB transport ownership state.")
    transport_status_parser.add_argument("transport")
    transport_status_parser.add_argument("--config", type=Path, help="Path to an AMPB config file.")
    transport_start_parser = transport_subcommands.add_parser("start", help="Start an AMPB-owned transport.")
    transport_start_parser.add_argument("transport")
    transport_start_parser.add_argument("--config", type=Path, help="Path to an AMPB config file.")
    transport_stop_parser = transport_subcommands.add_parser("stop", help="Stop an AMPB-owned transport.")
    transport_stop_parser.add_argument("transport")
    transport_stop_parser.add_argument("--config", type=Path, help="Path to an AMPB config file.")

    fixture_parser = subcommands.add_parser("fixture", help="Check AMPG fixture manifests.")
    fixture_subcommands = fixture_parser.add_subparsers(dest="fixture_command", required=True)
    fixture_check = fixture_subcommands.add_parser("check", help="Validate route expectations.")
    fixture_check.add_argument("manifest", type=Path)

    docs_parser = subcommands.add_parser("docs", help="Generate or check generated docs.")
    docs_subcommands = docs_parser.add_subparsers(dest="docs_command", required=True)
    docs_generate = docs_subcommands.add_parser("generate", help="Generate docs from code.")
    docs_generate.add_argument("--check", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.command == "route":
            return _cmd_route(args.url)
        if args.command == "plan":
            return _cmd_plan(args.url, config_path=args.config, platform=args.platform)
        if args.command == "open":
            return _cmd_open(
                args.url,
                consent=args.yes,
                dry_run=not args.launch,
                launch=args.launch,
                config_path=args.config,
                platform=args.platform,
            )
        if args.command == "inspect":
            return _cmd_inspect()
        if args.command == "transport":
            return _cmd_transport(args)
        if args.command == "fixture":
            return _cmd_fixture(args)
        if args.command == "docs":
            return _cmd_docs(args)
    except Exception as exc:  # noqa: BLE001
        print(f"AMPBROWSER status=error message={exc}", file=sys.stderr)
        return 1
    return 1


def _cmd_route(url: str) -> int:
    route = route_url(url)
    print(
        "AMPBROWSER_ROUTE "
        f"url={route.normalized} "
        f"transport={route.transport} "
        f"profile={route.profile} "
        f"reason=\"{route.reason}\""
    )
    return 0


def _cmd_plan(url: str, *, config_path: Path | None, platform: str | None) -> int:
    config = load_config(Path.cwd(), config_path)
    plan = plan_url(url, config=config, platform=platform)
    endpoint = plan.status.endpoint if plan.status else "-"
    running = str(plan.status.running).lower() if plan.status else "false"
    installed = str(plan.status.installed).lower() if plan.status else "false"
    prompt = plan.prompt.replace('"', "'") if plan.prompt else "-"
    print(
        "AMPBROWSER_PLAN "
        f"url={plan.route.normalized} "
        f"transport={plan.route.transport} "
        f"profile={plan.route.profile} "
        f"installed={installed} "
        f"running={running} "
        f"endpoint={endpoint} "
        f"platform={plan.platform_capability.platform} "
        f"platform_browse={plan.platform_capability.browse} "
        f"platform_manage={plan.platform_capability.manage} "
        f"policy={plan.policy_mode} "
        f"requires_consent={str(plan.requires_consent).lower()} "
        f"action=\"{plan.action}\" "
        f"prompt=\"{prompt}\""
    )
    return 0


def _cmd_open(
    url: str,
    *,
    consent: bool,
    dry_run: bool,
    launch: bool,
    config_path: Path | None,
    platform: str | None,
) -> int:
    config = load_config(Path.cwd(), config_path)
    open_plan = prepare_open(url, consent=consent, dry_run=dry_run, config=config, platform=platform)
    if launch:
        if open_plan.status == "setup-approved":
            transport_result = ensure_transport_ready(
                open_plan.browse_plan.route.transport,
                config=config,
                root=Path.cwd(),
                status=open_plan.browse_plan.status,
            )
            open_plan = replace(
                open_plan,
                dry_run=False,
                status="ready" if transport_result.ready else transport_result.status,
                message=transport_result.message,
                transport_setup_status=transport_result.status,
                transport_setup_provider=transport_result.provider,
                transport_setup_owned=transport_result.owned,
                transport_setup_pid=transport_result.pid,
                transport_setup_endpoint=transport_result.endpoint,
                transport_setup_message=transport_result.message,
            )
        open_plan = execute_open(open_plan, root=Path.cwd())
    browse_plan = open_plan.browse_plan
    setup_steps = "|".join(open_plan.setup_steps) if open_plan.setup_steps else "-"
    launch_spec = open_plan.launch_spec
    launch_command = shlex.join(launch_spec.command) if launch_spec else "-"
    runtime_path = launch_spec.runtime_path if launch_spec else "-"
    user_js_path = launch_spec.user_js_path if launch_spec else "-"
    message = _safe(open_plan.message)
    print(
        "AMPBROWSER_OPEN "
        f"url={browse_plan.route.normalized} "
        f"transport={browse_plan.route.transport} "
        f"profile={browse_plan.route.profile} "
        f"status={open_plan.status} "
        f"dry_run={str(open_plan.dry_run).lower()} "
        f"platform={browse_plan.platform_capability.platform} "
        f"platform_browse={browse_plan.platform_capability.browse} "
        f"platform_manage={browse_plan.platform_capability.manage} "
        f"policy={browse_plan.policy_mode} "
        f"requires_consent={str(browse_plan.requires_consent).lower()} "
        f"consent_granted={str(open_plan.consent_granted).lower()} "
        f"browser_pid={open_plan.browser_pid} "
        f"profile_path={open_plan.profile_path} "
        f"proxy={open_plan.proxy} "
        f"runtime_path={runtime_path} "
        f"user_js_path={user_js_path} "
        f"setup_prompt_title=\"{_safe(open_plan.setup_prompt_title)}\" "
        f"setup_prompt_body=\"{_safe(open_plan.setup_prompt_body)}\" "
        f"setup_prompt_approve_label=\"{_safe(open_plan.setup_prompt_approve_label)}\" "
        f"setup_prompt_approval_command=\"{_safe(open_plan.setup_prompt_approval_command)}\" "
        f"transport_setup_status={open_plan.transport_setup_status} "
        f"transport_setup_provider={open_plan.transport_setup_provider} "
        f"transport_setup_owned={str(open_plan.transport_setup_owned).lower()} "
        f"transport_setup_pid={open_plan.transport_setup_pid} "
        f"transport_setup_endpoint={open_plan.transport_setup_endpoint} "
        f"transport_setup_message=\"{_safe(open_plan.transport_setup_message)}\" "
        f"launch_command=\"{_safe(launch_command)}\" "
        f"setup_steps=\"{_safe(setup_steps)}\" "
        f"message=\"{message}\""
    )
    return 0


def _cmd_inspect() -> int:
    for status in inspect_transports():
        print(
            "AMPBROWSER_INSPECT "
            f"transport={status.transport} "
            f"installed={str(status.installed).lower()} "
            f"running={str(status.running).lower()} "
            f"adoptable={str(status.adoptable).lower()} "
            f"manage_supported={str(status.manage_supported).lower()} "
            f"endpoint={status.endpoint} "
            f"note=\"{status.note}\""
        )
    return 0


def _cmd_transport(args) -> int:
    config = load_config(Path.cwd(), args.config)
    if args.transport_command == "status":
        result = transport_status(args.transport, config=config, root=Path.cwd())
    elif args.transport_command == "start":
        result = ensure_transport_ready(args.transport, config=config, root=Path.cwd())
    elif args.transport_command == "stop":
        result = stop_managed_transport(args.transport, config=config, root=Path.cwd())
    else:
        return 1
    command = shlex.join(result.command) if result.command else "-"
    print(
        "AMPBROWSER_TRANSPORT "
        f"transport={result.transport} "
        f"provider={result.provider} "
        f"status={result.status} "
        f"ready={str(result.ready).lower()} "
        f"owned={str(result.owned).lower()} "
        f"pid={result.pid} "
        f"endpoint={result.endpoint} "
        f"state_dir={result.state_dir} "
        f"command=\"{_safe(command)}\" "
        f"message=\"{_safe(result.message)}\""
    )
    return 0


def _cmd_docs(args) -> int:
    if args.docs_command == "generate":
        changed = generate_docs(Path.cwd(), check=args.check)
        changed_text = ",".join(str(path) for path in changed) if changed else "-"
        mode = "check" if args.check else "write"
        print(f"AMPBROWSER_DOCS status=ok mode={mode} changed={changed_text}")
        return 0
    return 1


def _cmd_fixture(args) -> int:
    if args.fixture_command == "check":
        result = check_fixture_manifest(args.manifest)
        for check in result.checks:
            print(
                "AMPBROWSER_FIXTURE "
                f"site={check.site_id} "
                f"protocol={check.protocol} "
                f"route_match={check.route_match} "
                f"fixture_path={check.fixture_path} "
                f"url={check.url} "
                f"expected_transport={check.expected_transport} "
                f"actual_transport={check.actual_transport} "
                f"expected_profile={check.expected_profile} "
                f"actual_profile={check.actual_profile} "
                f"tier={check.tier} "
                f"identity={check.identity} "
                f"payments={check.payments} "
                f"realtime={str(check.realtime).lower()} "
                f"public_allowed={str(check.public_allowed).lower()} "
                f"status={check.status} "
                f"message=\"{_safe(check.message)}\""
            )
        print(
            "AMPBROWSER_FIXTURE_SUMMARY "
            f"site={result.site_id} "
            f"manifest={result.manifest_path} "
            f"checks={len(result.checks)} "
            f"status={'ok' if result.ok else 'fail'}"
        )
        return 0 if result.ok else 1
    return 1


def _safe(value: str) -> str:
    return value.replace('"', "'")
