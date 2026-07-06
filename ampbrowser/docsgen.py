from __future__ import annotations

from pathlib import Path

from .metadata import ROUTE_RULES, TRANSPORT_DEFINITIONS
from .platforms import PLATFORM_CAPABILITIES


GENERATED_DIR = Path("docs/generated")


def generate_docs(root: Path, *, check: bool = False) -> list[Path]:
    docs = {
        GENERATED_DIR / "route-rules.md": _route_rules_doc(),
        GENERATED_DIR / "transports.md": _transports_doc(),
        GENERATED_DIR / "platform-capabilities.md": _platform_capabilities_doc(),
    }
    changed: list[Path] = []
    for rel_path, content in docs.items():
        path = root / rel_path
        if path.exists() and path.read_text(encoding="utf-8") == content:
            continue
        changed.append(rel_path)
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if check and changed:
        names = ", ".join(str(path) for path in changed)
        raise RuntimeError(f"generated docs are stale: {names}")
    return changed


def _header(title: str) -> str:
    return (
        f"# {title}\n\n"
        "> Status: generated | Updated by `python3 -m ampbrowser docs generate` | Applies to: AMPB\n\n"
        "This file is generated from code. Do not edit it by hand.\n\n"
    )


def _route_rules_doc() -> str:
    rows = [
        "| Match | Transport | Profile | Note |",
        "| --- | --- | --- | --- |",
    ]
    for rule in ROUTE_RULES:
        rows.append(f"| `{rule.match}` | `{rule.transport}` | `{rule.profile}` | {rule.note} |")
    return _header("Generated Route Rules") + "\n".join(rows) + "\n"


def _transports_doc() -> str:
    rows = [
        "| Transport | Adopt Check | Managed State | Profile | Note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for transport in TRANSPORT_DEFINITIONS:
        rows.append(
            f"| `{transport.name}` | {transport.adopt_check} | `{transport.managed_state}` | "
            f"`{transport.profile}` | {transport.note} |"
        )
    return _header("Generated Transports") + "\n".join(rows) + "\n"


def _platform_capabilities_doc() -> str:
    rows = [
        "| Transport | Platform | Browse | Adopt | Manage | Install | Note |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for capability in PLATFORM_CAPABILITIES:
        rows.append(
            f"| `{capability.transport}` | `{capability.platform}` | `{capability.browse}` | "
            f"`{capability.adopt}` | `{capability.manage}` | `{capability.install}` | {capability.note} |"
        )
    return _header("Generated Platform Capabilities") + "\n".join(rows) + "\n"
