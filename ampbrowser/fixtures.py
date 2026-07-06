from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .routing import route_url


SUPPORTED_SCHEMAS = {"ampg.fixture-manifest.v1"}


@dataclass(frozen=True)
class FixtureCheck:
    site_id: str
    protocol: str
    url: str
    expected_transport: str
    actual_transport: str
    expected_profile: str
    actual_profile: str
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
    expected_profile = _string(checks, "profile")

    route = route_url(url)
    failures: list[str] = []
    if route.transport != expected_transport:
        failures.append(f"transport expected {expected_transport} got {route.transport}")
    if route.profile != expected_profile:
        failures.append(f"profile expected {expected_profile} got {route.profile}")

    return FixtureCheck(
        site_id=site_id,
        protocol=protocol,
        url=route.normalized,
        expected_transport=expected_transport,
        actual_transport=route.transport,
        expected_profile=expected_profile,
        actual_profile=route.profile,
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
