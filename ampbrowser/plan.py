from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig, default_config
from .routing import Route, route_url
from .transports import TransportStatus, inspect_transport


@dataclass(frozen=True)
class BrowsePlan:
    route: Route
    status: TransportStatus | None
    action: str
    requires_consent: bool = False
    prompt: str = ""
    policy_mode: str = "adopt-or-prompt-manage"


def plan_url(raw_url: str, *, config: AppConfig | None = None) -> BrowsePlan:
    config = config or default_config()
    route = route_url(raw_url)
    status = inspect_transport(route.transport)
    policy_mode = config.transport_mode(route.transport)

    if policy_mode == "disabled":
        return BrowsePlan(
            route=route,
            status=status,
            action=f"blocked by policy: {route.transport} disabled",
            policy_mode=policy_mode,
        )
    if route.transport in {"clearnet", "unknown"}:
        return BrowsePlan(
            route=route,
            status=status,
            action="open with clearnet profile",
            policy_mode=policy_mode,
        )
    if status and status.adoptable:
        return BrowsePlan(
            route=route,
            status=status,
            action="adopt existing transport",
            policy_mode=policy_mode,
        )
    if policy_mode == "adopt":
        return BrowsePlan(
            route=route,
            status=status,
            action=f"blocked by policy: {route.transport} mode is adopt",
            policy_mode=policy_mode,
        )
    if status and status.manage_supported:
        action = "prompt to start managed transport"
        prompt = (
            f"{route.transport} is not running. AMPB can start a managed {route.transport} "
            f"transport for {route.normalized}."
        )
        if not status.installed:
            action = "prompt to install and start managed transport"
            prompt = (
                f"{route.transport} is not installed or running. AMPB can install and start "
                f"a managed {route.transport} transport for {route.normalized}."
            )
        return BrowsePlan(
            route=route,
            status=status,
            action=action,
            requires_consent=True,
            prompt=prompt,
            policy_mode=policy_mode,
        )
    return BrowsePlan(
        route=route,
        status=status,
        action="blocked until adapter is configured",
        policy_mode=policy_mode,
    )
