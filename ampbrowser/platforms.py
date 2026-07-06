from __future__ import annotations

from dataclasses import dataclass
import sys


PLATFORM_CHOICES = ("desktop", "android", "ios")
MANAGED_SETUP_VALUES = {"ready", "planned", "foreground-only"}


@dataclass(frozen=True)
class PlatformCapability:
    transport: str
    platform: str
    browse: str
    adopt: str
    manage: str
    install: str
    note: str

    @property
    def can_manage_setup(self) -> bool:
        return self.manage in MANAGED_SETUP_VALUES


PLATFORM_CAPABILITIES = (
    PlatformCapability("clearnet", "desktop", "ready", "ready", "unsupported", "unsupported", "Use system browser or isolated desktop profile."),
    PlatformCapability("clearnet", "android", "ready", "ready", "unsupported", "unsupported", "Use Android browser shell, WebView, or Custom Tabs."),
    PlatformCapability("clearnet", "ios", "ready", "ready", "unsupported", "unsupported", "Use iOS browser shell with platform web constraints."),
    PlatformCapability("tor", "desktop", "ready", "ready", "planned", "planned", "Adopt local Tor or prompt before managed desktop daemon setup."),
    PlatformCapability("tor", "android", "planned", "planned", "planned", "planned", "Use an app-owned foreground service or compatible installed Tor provider."),
    PlatformCapability("tor", "ios", "foreground-only", "planned", "foreground-only", "constrained", "Plan for in-app foreground sessions; do not assume always-on background service."),
    PlatformCapability("i2p", "desktop", "ready", "ready", "planned", "planned", "Adopt local I2P proxy or prompt before managed desktop daemon setup."),
    PlatformCapability("i2p", "android", "planned", "planned", "planned", "planned", "Use an app-owned foreground service or compatible installed I2P provider."),
    PlatformCapability("i2p", "ios", "constrained", "planned", "foreground-only", "constrained", "Treat iOS I2P support as foreground-only until native adapter constraints are proven."),
    PlatformCapability("ipfs", "desktop", "ready", "ready", "planned", "planned", "Adopt local IPFS gateway or prompt before managed gateway setup."),
    PlatformCapability("ipfs", "android", "planned", "planned", "planned", "planned", "Use gateway-first IPFS browsing; embedded node support needs adapter proof."),
    PlatformCapability("ipfs", "ios", "constrained", "planned", "foreground-only", "constrained", "Use gateway-first IPFS browsing; embedded node support is constrained."),
    PlatformCapability("gemini", "desktop", "ready", "ready", "ready", "unsupported", "Built-in fetch/render path can be shared by desktop shell."),
    PlatformCapability("gemini", "android", "ready", "ready", "ready", "unsupported", "Built-in fetch/render path can be shared by Android shell."),
    PlatformCapability("gemini", "ios", "ready", "ready", "ready", "unsupported", "Built-in fetch/render path can be shared by iOS shell."),
    PlatformCapability("reticulum", "desktop", "planned", "planned", "planned", "planned", "Resilient/private networking adapter and interface checks are planned."),
    PlatformCapability("reticulum", "android", "planned", "planned", "planned", "planned", "Mobile resilient-network adapter should use explicit foreground service consent."),
    PlatformCapability("reticulum", "ios", "constrained", "planned", "foreground-only", "constrained", "Do not assume background Reticulum operation on iOS."),
    PlatformCapability("unknown", "desktop", "unsupported", "unsupported", "unsupported", "unsupported", "No platform route is available."),
    PlatformCapability("unknown", "android", "unsupported", "unsupported", "unsupported", "unsupported", "No platform route is available."),
    PlatformCapability("unknown", "ios", "unsupported", "unsupported", "unsupported", "unsupported", "No platform route is available."),
)


def detect_platform() -> str:
    if hasattr(sys, "getandroidapilevel"):
        return "android"
    if sys.platform in {"ios", "watchos", "tvos"}:
        return "ios"
    return "desktop"


def normalize_platform(platform: str | None) -> str:
    selected = platform or detect_platform()
    if selected not in PLATFORM_CHOICES:
        choices = ", ".join(PLATFORM_CHOICES)
        raise ValueError(f"platform must be one of: {choices}")
    return selected


def capability_for(transport: str, platform: str | None = None) -> PlatformCapability:
    selected = normalize_platform(platform)
    for capability in PLATFORM_CAPABILITIES:
        if capability.transport == transport and capability.platform == selected:
            return capability
    for capability in PLATFORM_CAPABILITIES:
        if capability.transport == "unknown" and capability.platform == selected:
            return capability
    raise ValueError(f"no capability for transport={transport} platform={selected}")
