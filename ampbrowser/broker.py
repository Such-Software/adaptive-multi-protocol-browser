from __future__ import annotations

from pathlib import Path

from .config import AppConfig
from .launch import OpenPlan, prepare_open
from .open_runner import launch_open_plan
from .routing import route_url


BROKER_TRANSPORTS = {"tor", "i2p"}


class BrokerRouteError(ValueError):
    pass


def open_brokered_url(
    raw_url: str,
    *,
    expected_transport: str,
    consent: bool,
    config: AppConfig,
    root: Path,
) -> OpenPlan:
    route = route_url(raw_url)
    if route.transport != expected_transport:
        raise BrokerRouteError(
            f"route transport {route.transport} does not match requested transport {expected_transport}"
        )
    if route.transport not in BROKER_TRANSPORTS:
        raise BrokerRouteError(f"{route.transport} is not supported by the desktop broker yet")

    open_plan = prepare_open(
        route.normalized,
        consent=consent,
        dry_run=False,
        config=config,
        platform="desktop",
    )
    return launch_open_plan(open_plan, config=config, root=root)
