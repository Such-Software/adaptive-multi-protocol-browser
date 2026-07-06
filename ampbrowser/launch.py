from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig, default_config
from .plan import BrowsePlan, plan_url


@dataclass(frozen=True)
class OpenPlan:
    browse_plan: BrowsePlan
    status: str
    dry_run: bool
    consent_granted: bool
    profile_path: str
    proxy: str
    setup_steps: tuple[str, ...]
    message: str


def prepare_open(
    raw_url: str,
    *,
    consent: bool = False,
    dry_run: bool = True,
    config: AppConfig | None = None,
    platform: str | None = None,
) -> OpenPlan:
    config = config or default_config()
    browse_plan = plan_url(raw_url, config=config, platform=platform)
    profile_path = config.profile_path(browse_plan.route.profile)
    proxy = _proxy_for(browse_plan)

    if browse_plan.action.startswith("blocked"):
        return OpenPlan(
            browse_plan=browse_plan,
            status="blocked",
            dry_run=dry_run,
            consent_granted=consent,
            profile_path=profile_path,
            proxy=proxy,
            setup_steps=(),
            message=browse_plan.action,
        )

    if browse_plan.requires_consent:
        setup_steps = _setup_steps(browse_plan)
        if not consent:
            return OpenPlan(
                browse_plan=browse_plan,
                status="consent-required",
                dry_run=dry_run,
                consent_granted=False,
                profile_path=profile_path,
                proxy=proxy,
                setup_steps=setup_steps,
                message=browse_plan.prompt,
            )
        return OpenPlan(
            browse_plan=browse_plan,
            status="setup-approved",
            dry_run=dry_run,
            consent_granted=True,
            profile_path=profile_path,
            proxy=proxy,
            setup_steps=setup_steps,
            message="first-use setup approved; execution is not implemented yet",
        )

    return OpenPlan(
        browse_plan=browse_plan,
        status="ready",
        dry_run=dry_run,
        consent_granted=consent,
        profile_path=profile_path,
        proxy=proxy,
        setup_steps=(),
        message="ready to open with isolated profile",
    )


def _proxy_for(browse_plan: BrowsePlan) -> str:
    if browse_plan.route.transport in {"tor", "i2p"} and browse_plan.status:
        return browse_plan.status.endpoint
    return "-"


def _setup_steps(browse_plan: BrowsePlan) -> tuple[str, ...]:
    if not browse_plan.status:
        return ()

    steps: list[str] = []
    platform = browse_plan.platform_capability.platform
    if not browse_plan.status.installed:
        if platform == "android":
            steps.append(f"install or enable Android {browse_plan.route.transport} provider")
        elif platform == "ios":
            steps.append(f"enable foreground iOS {browse_plan.route.transport} session")
        else:
            steps.append(f"install {browse_plan.route.transport}")
    if platform == "android":
        steps.append("start visible Android foreground service")
        steps.extend(
            [
                f"start managed Android {browse_plan.route.transport} transport",
                f"wait for {browse_plan.status.endpoint}",
            ]
        )
        return tuple(steps)
    elif platform == "ios":
        steps.append("start foreground-only iOS session")
        steps.extend(
            [
                f"start foreground-only iOS {browse_plan.route.transport} transport",
                f"wait for {browse_plan.status.endpoint}",
            ]
        )
        return tuple(steps)
    steps.extend([f"start managed {browse_plan.route.transport}", f"wait for {browse_plan.status.endpoint}"])
    return tuple(steps)
