# Architecture

> Status: draft | Updated 2026-07-07 | Applies to: AMPB contributors and integrators

AMPB is a browser orchestration layer for privacy, resilient-network, content-addressed,
and alternate-web transports. It keeps the routing, transport management, and profile
isolation decisions outside the browser engine until those contracts are stable.

## Operating Model

1. Normalize the requested URL.
2. Select a transport from scheme and host rules.
3. Inspect whether the required local transport is already running.
4. Adopt healthy existing transports.
5. If the selected transport is missing, show a first-use prompt before setup.
6. Start or install managed transports only after user consent.
7. Open the URL with the matching isolated profile.

## Main Components

- `ampbrowser.routing`: deterministic URL-to-transport rules.
- `ampbrowser.adapters`: transport ownership, setup, inspection, and health contracts.
- `ampbrowser.transports`: local readiness checks for Tor, I2P, IPFS, Reticulum, and Gemini.
- `ampbrowser.plan`: dry-run action planner for browser launches.
- `ampbrowser.launch`: side-effect-free launch specs and first-use consent state.
- `ampbrowser.platforms`: platform capability matrix for desktop, Android, and iOS.
- `ampbrowser.candidates`: evaluated transport candidates before active adapter support.
- `ampbrowser.docsgen`: generated public documentation from code-owned metadata.

## Browser Strategy

The first implementation should be Firefox-first without becoming a browser-engine fork
immediately. AMPB should control a hardened Firefox runtime, AMPB-owned profiles,
transport proxy policy, native transport setup, and health checks while the orchestration
contracts become stable.

Tor Browser compatibility is the high bar for `.onion` browsing. AMPB must not claim Tor
Browser equivalence until it tracks the relevant Tor Browser hardening, fingerprinting,
proxy, and update behavior. Chromium or CEF can remain a prototype fallback, but it is not
the main privacy-browser strategy.

The long-term browser can become a deeper Firefox or Tor Browser fork once the
orchestration surface is reliable: profile isolation is predictable, transport adoption is
boring, and generated fixtures from AMPG open without manual proxy setup.

Generated backend metadata lives in
[generated browser strategy](generated/browser-strategy.md).

## Relationship To AMPG

AMPG publishes protocol-specific site variants. AMPB opens those variants with the right
transport and profile. Wownero is the shared fixture for static publishing, while
interactive targets exercise sessions, dynamic assets, forms, and script policy.
