from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .docsgen import generate_docs
from .plan import plan_url
from .routing import route_url
from .transports import inspect_transports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ampbrowser")
    subcommands = parser.add_subparsers(dest="command", required=True)

    route_parser = subcommands.add_parser("route", help="Route a URL to a transport.")
    route_parser.add_argument("url")

    plan_parser = subcommands.add_parser("plan", help="Plan how a URL would be opened.")
    plan_parser.add_argument("url")

    subcommands.add_parser("inspect", help="Inspect local transport readiness.")

    docs_parser = subcommands.add_parser("docs", help="Generate or check generated docs.")
    docs_subcommands = docs_parser.add_subparsers(dest="docs_command", required=True)
    docs_generate = docs_subcommands.add_parser("generate", help="Generate docs from code.")
    docs_generate.add_argument("--check", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.command == "route":
            return _cmd_route(args.url)
        if args.command == "plan":
            return _cmd_plan(args.url)
        if args.command == "inspect":
            return _cmd_inspect()
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


def _cmd_plan(url: str) -> int:
    plan = plan_url(url)
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
        f"requires_consent={str(plan.requires_consent).lower()} "
        f"action=\"{plan.action}\" "
        f"prompt=\"{prompt}\""
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


def _cmd_docs(args) -> int:
    if args.docs_command == "generate":
        changed = generate_docs(Path.cwd(), check=args.check)
        changed_text = ",".join(str(path) for path in changed) if changed else "-"
        mode = "check" if args.check else "write"
        print(f"AMPBROWSER_DOCS status=ok mode={mode} changed={changed_text}")
        return 0
    return 1
