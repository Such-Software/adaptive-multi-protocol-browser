from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouteRule:
    match: str
    transport: str
    profile: str
    note: str


@dataclass(frozen=True)
class TransportDefinition:
    name: str
    adopt_check: str
    managed_state: str
    profile: str
    note: str


@dataclass(frozen=True)
class BrowserBackend:
    name: str
    role: str
    status: str
    platforms: str
    launch_mode: str
    privacy_posture: str
    note: str


ROUTE_RULES = (
    RouteRule("*.onion", "tor", "tor", "route through Tor SOCKS"),
    RouteRule("*.i2p", "i2p", "i2p", "route through I2P HTTP proxy"),
    RouteRule("ipfs://*, ipns://*, /ipfs/*, /ipns/*", "ipfs", "ipfs", "route through local IPFS gateway"),
    RouteRule("gemini://*", "gemini", "gemini", "fetch and render Gemtext"),
    RouteRule("rns://*, lxmf://*, nomad://*", "reticulum", "reticulum", "route to Reticulum adapter"),
    RouteRule("http://*, https://*", "clearnet", "clearnet", "ordinary web profile"),
)

TRANSPORT_DEFINITIONS = (
    TransportDefinition(
        "tor",
        "SOCKS on 127.0.0.1:9050",
        ".ampb/transports/tor",
        "tor",
        "Adopt existing Tor when healthy; otherwise prompt before managed setup.",
    ),
    TransportDefinition(
        "i2p",
        "HTTP proxy on 127.0.0.1:4444",
        ".ampb/transports/i2p",
        "i2p",
        "Adopt existing i2pd/I2P router when healthy; otherwise prompt before managed setup.",
    ),
    TransportDefinition(
        "ipfs",
        "HTTP gateway on 127.0.0.1:8080",
        ".ampb/transports/ipfs",
        "ipfs",
        "Adopt existing IPFS gateway when healthy; otherwise prompt before managed setup.",
    ),
    TransportDefinition(
        "gemini",
        "built-in renderer available",
        ".ampb/transports/gemini",
        "gemini",
        "No daemon required for static Gemtext browsing.",
    ),
    TransportDefinition(
        "reticulum",
        "RNS tools and configured interfaces",
        ".ampb/transports/reticulum",
        "reticulum",
        "Adapter planned for resilient/private routing; physical/link-layer setup may require operator config.",
    ),
)

BROWSER_BACKENDS = (
    BrowserBackend(
        "hardened-firefox",
        "primary web runtime",
        "planned",
        "desktop, android",
        "managed profile, policy, and native transport launcher",
        "strong baseline; track Firefox ESR and Tor Browser hardening choices",
        "Default AMPB web runtime before a full browser fork.",
    ),
    BrowserBackend(
        "tor-browser-compatible",
        "tor-hardened target",
        "planned",
        "desktop, android",
        "adopt, launch, or fork after transport contracts are stable",
        "highest Tor web target; do not claim equivalence until Tor Browser patches are tracked",
        "Path toward real Tor Browser-grade behavior for .onion browsing.",
    ),
    BrowserBackend(
        "webkit-ios-shell",
        "ios runtime",
        "planned",
        "ios",
        "native shell with embedded transports and isolated web views",
        "platform constrained; avoid clearnet fallback and isolate transport state",
        "Required for App Store-style iOS builds outside special browser-engine entitlements.",
    ),
    BrowserBackend(
        "gemini-native-viewer",
        "alternate-web viewer",
        "planned",
        "desktop, android, ios",
        "built-in fetch and render path",
        "no web engine or shared browser storage required",
        "Used for Gemini and similar lightweight document transports.",
    ),
    BrowserBackend(
        "chromium-cef",
        "prototype fallback",
        "fallback",
        "desktop",
        "profile launcher only when Firefox path is blocked",
        "not a Tor Browser privacy baseline",
        "Allowed for experiments, but not the main privacy-browser strategy.",
    ),
)
