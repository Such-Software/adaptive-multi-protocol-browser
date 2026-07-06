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


ROUTE_RULES = (
    RouteRule("*.onion", "tor", "tor", "route through Tor SOCKS"),
    RouteRule("*.i2p", "i2p", "i2p", "route through I2P HTTP proxy"),
    RouteRule("gemini://*", "gemini", "gemini", "fetch and render Gemtext"),
    RouteRule("rns://*, lxmf://*, nomad://*", "reticulum", "reticulum", "route through Reticulum adapter"),
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
        "Adapter planned; physical/link-layer setup may require operator config.",
    ),
)
