from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class Route:
    original: str
    normalized: str
    transport: str
    profile: str
    reason: str


def route_url(raw_url: str) -> Route:
    normalized = _normalize_url(raw_url)
    parsed = urlparse(normalized)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()

    if scheme == "gemini":
        return Route(raw_url, normalized, "gemini", "gemini", "gemini scheme")
    if scheme in {"rns", "lxmf", "nomad"}:
        return Route(raw_url, normalized, "reticulum", "reticulum", f"{scheme} scheme")
    if host.endswith(".onion"):
        return Route(raw_url, normalized, "tor", "tor", ".onion host")
    if host.endswith(".i2p"):
        return Route(raw_url, normalized, "i2p", "i2p", ".i2p host")
    if scheme in {"http", "https"}:
        return Route(raw_url, normalized, "clearnet", "clearnet", "http(s) URL")
    return Route(raw_url, normalized, "unknown", "unknown", "no route rule matched")


def _normalize_url(raw_url: str) -> str:
    value = raw_url.strip()
    if "://" not in value and not value.startswith(("rns:", "lxmf:")):
        value = "https://" + value
    return value
