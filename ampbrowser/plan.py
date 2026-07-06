from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig, default_config
from .platforms import PlatformCapability, capability_for
from .routing import Route, route_url
from .transports import TransportStatus, inspect_transport


@dataclass(frozen=True)
class BrowsePlan:
    route: Route
    status: TransportStatus | None
    platform_capability: PlatformCapability
    action: str
    requires_consent: bool = False
    prompt: str = ""
    policy_mode: str = "adopt-or-prompt-manage"


def plan_url(
    raw_url: str,
    *,
    config: AppConfig | None = None,
    platform: str | None = None,
) -> BrowsePlan:
    config = config or default_config()
    route = route_url(raw_url)
    status = inspect_transport(route.transport)
    policy_mode = config.transport_mode(route.transport)
    platform_capability = capability_for(route.transport, platform)

    if platform_capability.browse == "unsupported":
        return BrowsePlan(
            route=route,
            status=status,
            platform_capability=platform_capability,
            action=f"blocked by platform: {route.transport} unsupported on {platform_capability.platform}",
            policy_mode=policy_mode,
        )

    if policy_mode == "disabled":
        return BrowsePlan(
            route=route,
            status=status,
            platform_capability=platform_capability,
            action=f"blocked by policy: {route.transport} disabled",
            policy_mode=policy_mode,
        )
    if route.transport in {"clearnet", "unknown"}:
        return BrowsePlan(
            route=route,
            status=status,
            platform_capability=platform_capability,
            action="open with clearnet profile",
            policy_mode=policy_mode,
        )
    if status and status.adoptable:
        return BrowsePlan(
            route=route,
            status=status,
            platform_capability=platform_capability,
            action="adopt existing transport",
            policy_mode=policy_mode,
        )
    if policy_mode == "adopt":
        return BrowsePlan(
            route=route,
            status=status,
            platform_capability=platform_capability,
            action=f"blocked by policy: {route.transport} mode is adopt",
            policy_mode=policy_mode,
        )
    if status and status.manage_supported and not platform_capability.can_manage_setup:
        return BrowsePlan(
            route=route,
            status=status,
            platform_capability=platform_capability,
            action=(
                f"blocked by platform: {route.transport} managed setup is "
                f"{platform_capability.manage} on {platform_capability.platform}"
            ),
            policy_mode=policy_mode,
        )
    if status and status.manage_supported:
        if platform_capability.manage == "foreground-only":
            action = "prompt to start foreground-only transport session"
            prompt = (
                f"{route.transport} is not running. AMPB can start a foreground-only "
                f"{route.transport} session for {route.normalized} on {platform_capability.platform}."
            )
        else:
            action = "prompt to start managed transport"
            prompt = (
                f"{route.transport} is not running. AMPB can start a managed {route.transport} "
                f"transport for {route.normalized}."
            )
        if not status.installed:
            if platform_capability.manage == "foreground-only":
                action = "prompt to enable foreground-only transport session"
                prompt = (
                    f"{route.transport} is not available. AMPB can enable a foreground-only "
                    f"{route.transport} session for {route.normalized} on {platform_capability.platform}."
                )
            else:
                action = "prompt to install and start managed transport"
                prompt = (
                    f"{route.transport} is not installed or running. AMPB can install and start "
                    f"a managed {route.transport} transport for {route.normalized}."
                )
        return BrowsePlan(
            route=route,
            status=status,
            platform_capability=platform_capability,
            action=action,
            requires_consent=True,
            prompt=prompt,
            policy_mode=policy_mode,
        )
    return BrowsePlan(
        route=route,
        status=status,
        platform_capability=platform_capability,
        action="blocked until adapter is configured",
        policy_mode=policy_mode,
    )
