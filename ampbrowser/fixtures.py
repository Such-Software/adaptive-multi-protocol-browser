from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .interaction_policy import interaction_failures
from .routing import route_url


SUPPORTED_SCHEMAS = {"ampg.fixture-manifest.v1", "ampg.fixture-manifest.v2"}


@dataclass(frozen=True)
class FixtureCheck:
    site_id: str
    protocol: str
    route_match: str
    fixture_path: str
    url: str
    expected_transport: str
    actual_transport: str
    expected_context: str
    actual_context: str
    expected_isolation: str
    actual_isolation: str
    tier: str
    identity: str
    payments: str
    realtime: bool
    public_allowed: bool
    status: str
    message: str


@dataclass(frozen=True)
class FixtureCheckResult:
    manifest_path: Path
    schema: str
    site_id: str
    checks: tuple[FixtureCheck, ...]

    @property
    def ok(self) -> bool:
        return all(check.status == "ok" for check in self.checks)


def check_fixture_manifest(path: Path) -> FixtureCheckResult:
    data = _load_manifest(path)
    schema = _string(data, "schema")
    if schema not in SUPPORTED_SCHEMAS:
        raise ValueError(f"{path}: unsupported manifest schema {schema!r}")

    site = data.get("site")
    if not isinstance(site, dict):
        raise ValueError(f"{path}: missing site table")
    site_id = _string(site, "id")

    fixtures = data.get("fixtures")
    if not isinstance(fixtures, list):
        raise ValueError(f"{path}: fixtures must be a list")

    checks = tuple(_check_fixture(site_id, fixture, path) for fixture in fixtures)
    return FixtureCheckResult(
        manifest_path=path,
        schema=schema,
        site_id=site_id,
        checks=checks,
    )


def _check_fixture(site_id: str, fixture: Any, path: Path) -> FixtureCheck:
    if not isinstance(fixture, dict):
        raise ValueError(f"{path}: fixture entries must be tables")
    protocol = _string(fixture, "protocol")
    url = _string(fixture, "url")
    checks = fixture.get("checks")
    if not isinstance(checks, dict):
        raise ValueError(f"{path}: {protocol}: missing checks table")
    expected_transport = _string(checks, "transport")
    expected_context = (
        _string(checks, "context")
        if "context" in checks
        else _string(checks, "profile")
    )
    expected_isolation = _optional_string(checks, "isolation", "transport-context")
    interaction = _interaction_policy(fixture)
    route_metadata = _route_metadata(fixture)

    route = route_url(url)
    actual_isolation = "transport-context"
    failures: list[str] = []
    if route.transport != expected_transport:
        failures.append(f"transport expected {expected_transport} got {route.transport}")
    if route.profile != expected_context:
        failures.append(f"context expected {expected_context} got {route.profile}")
    if actual_isolation != expected_isolation:
        failures.append(f"isolation expected {expected_isolation} got {actual_isolation}")
    failures.extend(
        interaction_failures(
            expected_transport,
            tier=interaction["tier"],
            identity=interaction["identity"],
            payments=interaction["payments"],
            realtime=interaction["realtime"],
            public_allowed=interaction["public_allowed"],
        )
    )

    return FixtureCheck(
        site_id=site_id,
        protocol=protocol,
        route_match=route_metadata["match"],
        fixture_path=route_metadata["fixture_path"],
        url=route.normalized,
        expected_transport=expected_transport,
        actual_transport=route.transport,
        expected_context=expected_context,
        actual_context=route.profile,
        expected_isolation=expected_isolation,
        actual_isolation=actual_isolation,
        tier=interaction["tier"],
        identity=interaction["identity"],
        payments=interaction["payments"],
        realtime=interaction["realtime"],
        public_allowed=interaction["public_allowed"],
        status="fail" if failures else "ok",
        message="; ".join(failures) if failures else "route matches",
    )


def _load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: manifest must be a JSON object")
    return data


def _string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing required string field {key!r}")
    return value


def _interaction_policy(fixture: dict[str, Any]) -> dict[str, Any]:
    raw = fixture.get("interaction", {})
    if not isinstance(raw, dict):
        raise ValueError(f"{fixture.get('protocol', 'fixture')}: interaction must be a table")
    return {
        "tier": _optional_string(raw, "tier", "static"),
        "identity": _optional_string(raw, "identity", "none"),
        "payments": _optional_string(raw, "payments", "none"),
        "realtime": _optional_bool(raw, "realtime", False),
        "public_allowed": _optional_bool(raw, "public_allowed", True),
    }


def _route_metadata(fixture: dict[str, Any]) -> dict[str, str]:
    raw = fixture.get("route", {})
    if not isinstance(raw, dict):
        raise ValueError(f"{fixture.get('protocol', 'fixture')}: route must be a table")
    return {
        "match": _optional_string(raw, "match", "/"),
        "fixture_path": _optional_string(raw, "fixture_path", "/"),
    }


def _optional_string(data: dict[str, Any], key: str, default: str) -> str:
    value = data.get(key, default)
    if not isinstance(value, str) or not value:
        raise ValueError(f"interaction.{key} must be a non-empty string")
    return value


def _optional_bool(data: dict[str, Any], key: str, default: bool) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"interaction.{key} must be true or false")
    return value
