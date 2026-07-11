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


@dataclass(frozen=True)
class ProviderSourceDefinition:
    source: str
    discovery: str
    lifecycle: str
    platforms: str
    note: str


@dataclass(frozen=True)
class TransportProviderDefinition:
    transport: str
    provider: str
    sources: tuple[str, ...]
    endpoint: str
    status: str
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
        "ampb-gecko-desktop",
        "primary desktop runtime",
        "planned",
        "desktop",
        "bundled Firefox/Gecko-lineage app with one window and AMPB-owned transport contexts",
        "no system browser dependency; track Firefox ESR, Tor Browser, and Mullvad hardening choices",
        "Default desktop runtime; users should not need Firefox installed.",
    ),
    BrowserBackend(
        "ampb-geckoview-android",
        "primary android runtime",
        "planned",
        "android",
        "bundled GeckoView/Fenix/Tor Browser Android-lineage app with foreground transports",
        "no system browser dependency; app owns context, proxy policy, and transport lifecycle",
        "Default Android runtime for real mobile AMPB.",
    ),
    BrowserBackend(
        "ampb-webkit-ios",
        "ios runtime",
        "planned",
        "ios",
        "bundled iOS app shell with WebKit views and embedded transport runtimes",
        "platform constrained; avoid clearnet fallback and isolate transport state",
        "Default iOS path unless alternate browser-engine entitlements become practical.",
    ),
    BrowserBackend(
        "tor-browser-lineage",
        "tor-hardened target",
        "planned",
        "desktop, android",
        "reuse or track Tor Browser patches after AMPB transport contracts are stable",
        "highest Tor web target; do not claim equivalence until Tor Browser patches are tracked",
        "Path toward real Tor Browser-grade behavior for .onion browsing.",
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
)

PROVIDER_SOURCE_DEFINITIONS = (
    ProviderSourceDefinition(
        "configured",
        "explicit config or environment variable",
        "operator override; AMPB owns profile policy but not the binary provenance",
        "desktop, android, ios",
        "Used for development, custom bundles, and reviewed advanced installs.",
    ),
    ProviderSourceDefinition(
        "bundled-sidecar",
        "provider binary shipped with AMPB or the build workspace",
        "AMPB-owned process and isolated state",
        "desktop, android",
        "Default desktop target for Tor, I2P, IPFS, Reticulum, and similar daemon-style transports.",
    ),
    ProviderSourceDefinition(
        "embedded-library",
        "transport library linked into the app process",
        "AMPB-owned foreground session and app-private state",
        "android, ios",
        "Preferred mobile shape when platform policy makes sidecar daemons awkward.",
    ),
    ProviderSourceDefinition(
        "system-adopted",
        "healthy local proxy or service already running",
        "operator-owned service; AMPB only routes browser traffic to it",
        "desktop, android",
        "Keeps power users and existing deployments working without duplicate daemons.",
    ),
    ProviderSourceDefinition(
        "system-package",
        "known package manager install such as brew, apt, pkg, or platform provider",
        "installed only after user consent, then run with AMPB-owned state",
        "desktop, android",
        "Fallback when the app did not ship that provider yet.",
    ),
    ProviderSourceDefinition(
        "builtin-renderer",
        "browser-native renderer or fetch path",
        "AMPB-owned code path with no external daemon",
        "desktop, android, ios",
        "Used for Gemini and other lightweight document transports.",
    ),
)

TRANSPORT_PROVIDER_DEFINITIONS = (
    TransportProviderDefinition(
        "tor",
        "arti/tor",
        ("configured", "bundled-sidecar", "embedded-library", "system-adopted", "system-package"),
        "socks5://127.0.0.1:9050",
        "active",
        "Desktop uses managed Arti/Tor sidecars today; mobile should prefer embedded or app-owned foreground providers.",
    ),
    TransportProviderDefinition(
        "i2p",
        "i2pd/i2p-router",
        ("configured", "bundled-sidecar", "embedded-library", "system-adopted", "system-package"),
        "http://127.0.0.1:4444",
        "active",
        "Desktop can adopt or manage i2pd; mobile provider packaging is planned behind the same contract.",
    ),
    TransportProviderDefinition(
        "gemini",
        "gemini-native-viewer",
        ("builtin-renderer",),
        "builtin://gemtext-renderer",
        "planned",
        "No daemon is required once the built-in fetch/render path exists.",
    ),
    TransportProviderDefinition(
        "ipfs",
        "kubo/ipfs",
        ("configured", "bundled-sidecar", "system-adopted", "system-package"),
        "http://127.0.0.1:8080",
        "planned",
        "Content-addressed browsing uses the same provider lifecycle without treating IPFS as anonymity.",
    ),
    TransportProviderDefinition(
        "reticulum",
        "rnsd/rnstatus",
        ("configured", "bundled-sidecar", "system-adopted", "system-package"),
        "rns://local",
        "planned",
        "Reticulum browsing may still need operator-owned physical or link-layer interface setup.",
    ),
)
