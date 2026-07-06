from __future__ import annotations

from dataclasses import dataclass


TIER_ORDER = {
    "static": 0,
    "interactive-lite": 1,
    "identity": 2,
    "transactional": 3,
    "realtime": 4,
    "internal": 5,
}


@dataclass(frozen=True)
class TransportInteractionPolicy:
    transport: str
    max_tier: str
    identities: tuple[str, ...]
    payments: tuple[str, ...]
    realtime: str


TRANSPORT_POLICIES = {
    "clearnet": TransportInteractionPolicy(
        "clearnet",
        "realtime",
        ("none", "http-session", "siwe"),
        ("none", "server-invoice", "wallet-signature"),
        "yes",
    ),
    "tor": TransportInteractionPolicy(
        "tor",
        "transactional",
        ("none", "http-session", "siwe"),
        ("none", "server-invoice", "wallet-signature"),
        "private-only",
    ),
    "i2p": TransportInteractionPolicy(
        "i2p",
        "transactional",
        ("none", "http-session", "siwe"),
        ("none", "server-invoice", "wallet-signature"),
        "private-only",
    ),
    "gemini": TransportInteractionPolicy(
        "gemini",
        "interactive-lite",
        ("none", "signed-link"),
        ("none", "static-instructions"),
        "no",
    ),
    "ipfs": TransportInteractionPolicy(
        "ipfs",
        "static",
        ("none",),
        ("none", "static-instructions"),
        "no",
    ),
    "reticulum": TransportInteractionPolicy(
        "reticulum",
        "interactive-lite",
        ("none", "signed-link"),
        ("none", "static-instructions"),
        "research",
    ),
}


def interaction_failures(
    transport: str,
    *,
    tier: str,
    identity: str,
    payments: str,
    realtime: bool,
    public_allowed: bool,
) -> list[str]:
    failures: list[str] = []
    policy = TRANSPORT_POLICIES.get(transport)
    if not policy:
        return [f"no interaction policy for transport {transport}"]
    if not public_allowed:
        failures.append("fixture is not public_allowed")
    if tier not in TIER_ORDER:
        failures.append(f"unknown tier {tier}")
    elif TIER_ORDER[tier] > TIER_ORDER[policy.max_tier]:
        failures.append(f"tier {tier} exceeds {transport} max {policy.max_tier}")
    if identity not in policy.identities:
        failures.append(f"identity {identity} not allowed on {transport}")
    if payments not in policy.payments:
        failures.append(f"payments {payments} not allowed on {transport}")
    if realtime and policy.realtime not in {"yes", "private-only", "research"}:
        failures.append(f"realtime not allowed on {transport}")
    return failures
