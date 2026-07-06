from __future__ import annotations

from dataclasses import dataclass
import shutil
import socket


@dataclass(frozen=True)
class TransportStatus:
    transport: str
    installed: bool
    running: bool
    endpoint: str
    adoptable: bool
    manage_supported: bool
    note: str


TRANSPORTS = ("tor", "i2p", "reticulum", "gemini")


def inspect_transports() -> list[TransportStatus]:
    return [
        _inspect_tor(),
        _inspect_i2p(),
        _inspect_reticulum(),
        _inspect_gemini(),
    ]


def inspect_transport(name: str) -> TransportStatus | None:
    for status in inspect_transports():
        if status.transport == name:
            return status
    return None


def _inspect_tor() -> TransportStatus:
    installed = shutil.which("tor") is not None
    running = _can_connect("127.0.0.1", 9050)
    return TransportStatus(
        transport="tor",
        installed=installed,
        running=running,
        endpoint="socks5://127.0.0.1:9050",
        adoptable=running,
        manage_supported=True,
        note="Tor SOCKS proxy",
    )


def _inspect_i2p() -> TransportStatus:
    installed = shutil.which("i2pd") is not None or shutil.which("i2prouter") is not None
    running = _can_connect("127.0.0.1", 4444)
    return TransportStatus(
        transport="i2p",
        installed=installed,
        running=running,
        endpoint="http://127.0.0.1:4444",
        adoptable=running,
        manage_supported=True,
        note="I2P HTTP proxy",
    )


def _inspect_reticulum() -> TransportStatus:
    installed = any(shutil.which(command) for command in ("rnsd", "rnstatus", "rnodeconf"))
    return TransportStatus(
        transport="reticulum",
        installed=installed,
        running=False,
        endpoint="rns://local",
        adoptable=False,
        manage_supported=False,
        note="Reticulum adapter is planned; interface readiness needs explicit config",
    )


def _inspect_gemini() -> TransportStatus:
    return TransportStatus(
        transport="gemini",
        installed=True,
        running=True,
        endpoint="builtin://gemtext-renderer",
        adoptable=True,
        manage_supported=True,
        note="Built-in Gemtext fetch/render path",
    )


def _can_connect(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False
