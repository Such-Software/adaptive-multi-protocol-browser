from __future__ import annotations

from dataclasses import dataclass

from .routing import Route, route_url
from .transports import TransportStatus, inspect_transport


@dataclass(frozen=True)
class BrowsePlan:
    route: Route
    status: TransportStatus | None
    action: str
    requires_consent: bool = False
    prompt: str = ""


def plan_url(raw_url: str) -> BrowsePlan:
    route = route_url(raw_url)
    status = inspect_transport(route.transport)
    if route.transport in {"clearnet", "unknown"}:
        return BrowsePlan(route=route, status=status, action="open with clearnet profile")
    if status and status.adoptable:
        return BrowsePlan(route=route, status=status, action="adopt existing transport")
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
        )
    return BrowsePlan(route=route, status=status, action="blocked until adapter is configured")
