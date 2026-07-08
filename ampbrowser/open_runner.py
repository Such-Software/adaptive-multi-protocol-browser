from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .config import AppConfig
from .launch import OpenPlan, execute_open
from .transport_manager import ensure_transport_ready


def launch_open_plan(open_plan: OpenPlan, *, config: AppConfig, root: Path) -> OpenPlan:
    if open_plan.status == "setup-approved":
        transport_result = ensure_transport_ready(
            open_plan.browse_plan.route.transport,
            config=config,
            root=root,
            status=open_plan.browse_plan.status,
        )
        open_plan = replace(
            open_plan,
            dry_run=False,
            status="ready" if transport_result.ready else transport_result.status,
            message=transport_result.message,
            transport_setup_status=transport_result.status,
            transport_setup_provider=transport_result.provider,
            transport_setup_provider_source=transport_result.provider_source,
            transport_setup_owned=transport_result.owned,
            transport_setup_pid=transport_result.pid,
            transport_setup_endpoint=transport_result.endpoint,
            transport_setup_message=transport_result.message,
        )
    return execute_open(open_plan, root=root)
