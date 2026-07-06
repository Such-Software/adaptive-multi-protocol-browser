from __future__ import annotations

from dataclasses import dataclass

from .plan import BrowsePlan, plan_url


PROFILE_ROOT = ".ampb/profiles"


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


def prepare_open(raw_url: str, *, consent: bool = False, dry_run: bool = True) -> OpenPlan:
    browse_plan = plan_url(raw_url)
    profile_path = f"{PROFILE_ROOT}/{browse_plan.route.profile}"
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
    if not browse_plan.status.installed:
        steps.append(f"install {browse_plan.route.transport}")
    steps.extend(
        [
            f"start managed {browse_plan.route.transport}",
            f"wait for {browse_plan.status.endpoint}",
        ]
    )
    return tuple(steps)
