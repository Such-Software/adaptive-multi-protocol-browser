from __future__ import annotations

from pathlib import Path

from .adapters import ADAPTERS
from .candidates import CANDIDATE_TRANSPORTS
from .metadata import BROWSER_BACKENDS, ROUTE_RULES, TRANSPORT_DEFINITIONS
from .metadata import PROVIDER_SOURCE_DEFINITIONS, TRANSPORT_PROVIDER_DEFINITIONS
from .platforms import PLATFORM_CAPABILITIES


GENERATED_DIR = Path("docs/generated")


def generate_docs(root: Path, *, check: bool = False) -> list[Path]:
    docs = {
        GENERATED_DIR / "route-rules.md": _route_rules_doc(),
        GENERATED_DIR / "transports.md": _transports_doc(),
        GENERATED_DIR / "adapters.md": _adapters_doc(),
        GENERATED_DIR / "candidate-transports.md": _candidate_transports_doc(),
        GENERATED_DIR / "platform-capabilities.md": _platform_capabilities_doc(),
        GENERATED_DIR / "browser-strategy.md": _browser_strategy_doc(),
        GENERATED_DIR / "provider-sources.md": _provider_sources_doc(),
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


def _adapters_doc() -> str:
    rows = [
        "| Adapter | Endpoint | Adopt Check | Install Strategy | Start Strategy | Stop Policy | Note |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for adapter in ADAPTERS.values():
        rows.append(
            f"| `{adapter.name}` | `{adapter.endpoint}` | {adapter.adopt_check} | "
            f"{adapter.install_strategy} | {adapter.start_strategy} | {adapter.stop_policy} | {adapter.note} |"
        )
    return _header("Generated Transport Adapters") + "\n".join(rows) + "\n"


def _candidate_transports_doc() -> str:
    rows = [
        "| Candidate | Role | Status | Routes | Browser Fit | Publisher Fit | Mobile Fit | Source | Note |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for candidate in CANDIDATE_TRANSPORTS:
        routes = ", ".join(f"`{route}`" for route in candidate.route_examples)
        rows.append(
            f"| `{candidate.name}` | {candidate.role} | `{candidate.status}` | {routes} | "
            f"{candidate.browser_fit} | {candidate.publisher_fit} | {candidate.mobile_fit} | "
            f"[source]({candidate.source}) | {candidate.note} |"
        )
    return _header("Generated Candidate Transports") + "\n".join(rows) + "\n"


def _browser_strategy_doc() -> str:
    rows = [
        "| Backend | Role | Status | Platforms | Launch Mode | Privacy Posture | Note |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for backend in BROWSER_BACKENDS:
        rows.append(
            f"| `{backend.name}` | {backend.role} | `{backend.status}` | {backend.platforms} | "
            f"{backend.launch_mode} | {backend.privacy_posture} | {backend.note} |"
        )
    return _header("Generated Browser Strategy") + "\n".join(rows) + "\n"


def _provider_sources_doc() -> str:
    sections = [_header("Generated Provider Sources")]
    sections.append("## Source Types\n")
    sections.append("| Source | Discovery | Lifecycle | Platforms | Note |")
    sections.append("| --- | --- | --- | --- | --- |")
    for source in PROVIDER_SOURCE_DEFINITIONS:
        sections.append(
            f"| `{source.source}` | {source.discovery} | {source.lifecycle} | "
            f"{source.platforms} | {source.note} |"
        )
    sections.append("")

    sections.append("## Transport Providers\n")
    sections.append("| Transport | Provider | Sources | Endpoint | Status | Note |")
    sections.append("| --- | --- | --- | --- | --- | --- |")
    for provider in TRANSPORT_PROVIDER_DEFINITIONS:
        sources = ", ".join(f"`{source}`" for source in provider.sources)
        sections.append(
            f"| `{provider.transport}` | `{provider.provider}` | {sources} | "
            f"`{provider.endpoint}` | `{provider.status}` | {provider.note} |"
        )
    sections.append("")
    return "\n".join(sections)
