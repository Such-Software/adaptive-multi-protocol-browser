from __future__ import annotations

from .adapters import ADAPTERS, TransportStatus


TRANSPORTS = tuple(ADAPTERS)


def inspect_transports() -> list[TransportStatus]:
    return [adapter.inspect() for adapter in ADAPTERS.values()]


def inspect_transport(name: str) -> TransportStatus | None:
    for status in inspect_transports():
        if status.transport == name:
            return status
    return None
