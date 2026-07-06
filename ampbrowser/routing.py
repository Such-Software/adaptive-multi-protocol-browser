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
    path_route = _route_path_address(raw_url)
    if path_route:
        return path_route

    normalized = _normalize_url(raw_url)
    parsed = urlparse(normalized)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()

    if scheme == "gemini":
        return Route(raw_url, normalized, "gemini", "gemini", "gemini scheme")
    if scheme in {"ipfs", "ipns"}:
        return Route(raw_url, normalized, "ipfs", "ipfs", f"{scheme} scheme")
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
    if "://" not in value and not value.startswith(("rns:", "lxmf:", "ipfs:", "ipns:")):
        value = "https://" + value
    return value


def _route_path_address(raw_url: str) -> Route | None:
    value = raw_url.strip()
    if value.startswith("/ipfs/"):
        cid = value.removeprefix("/ipfs/").strip("/")
        normalized = f"ipfs://{cid}" if cid else "ipfs://"
        return Route(raw_url, normalized, "ipfs", "ipfs", "/ipfs path")
    if value.startswith("/ipns/"):
        name = value.removeprefix("/ipns/").strip("/")
        normalized = f"ipns://{name}" if name else "ipns://"
        return Route(raw_url, normalized, "ipfs", "ipfs", "/ipns path")
    return None
