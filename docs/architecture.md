# Architecture

> Status: draft | Updated 2026-07-11 | Applies to: AMPB contributors and integrators

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

The clearnet entry profile is a broker, not a mixed-network profile. It uses direct
clearnet networking. Its extension blocks all `.onion` and `.i2p` requests from that
profile. For a top-level navigation, it asks a token-gated loopback helper to apply the
normal route and consent policy, then opens the destination in a separate transport
profile and browser process.

## Main Components

- `ampbrowser.routing`: deterministic URL-to-transport rules.
- `ampbrowser.adapters`: transport ownership, setup, inspection, and health contracts.
- `ampbrowser.transports`: local readiness checks for Tor, I2P, IPFS, Reticulum, and Gemini.
- `ampbrowser.plan`: dry-run action planner for browser launches.
- `ampbrowser.broker`: validated handoff from the clearnet entry profile to an isolated
  transport profile.
- `ampbrowser.launch`: side-effect-free launch specs and first-use consent state.
- `ampbrowser.platforms`: platform capability matrix for desktop, Android, and iOS.
- `ampbrowser.candidates`: evaluated transport candidates before active adapter support.
- `ampbrowser.docsgen`: generated public documentation from code-owned metadata.

## Browser Strategy

The first implementation should ship an AMPB-owned browser runtime, not attach to the
host system browser. Desktop AMPB should be a bundled Firefox/Gecko-lineage app with
AMPB-owned profiles, transport proxy policy, native transport setup, and health checks.
Android AMPB should use a bundled GeckoView/Fenix/Tor Browser Android-lineage runtime
with visible foreground transport services.

Tor Browser compatibility is the high bar for `.onion` browsing. AMPB must not claim Tor
Browser equivalence until it tracks the relevant Tor Browser hardening, fingerprinting,
proxy, and update behavior. AMPB should not depend on system Firefox, system Chrome, or
the user's default browser.

The long-term browser can become a deeper Firefox, GeckoView, or Tor Browser fork once
the orchestration surface is reliable: profile isolation is predictable, transport adoption
is boring, and generated fixtures from AMPG open without manual proxy setup.

Generated backend metadata lives in
[generated browser strategy](generated/browser-strategy.md).

The first implementation path is documented in [desktop vertical](desktop-vertical.md).

## Isolation Boundaries

- Browser storage is isolated by transport profile.
- Transport runtime state is isolated under AMPB-owned transport directories when AMPB
  manages the daemon.
- A transport profile remains sticky: ordinary navigation stays in that profile and uses
  its configured proxy until the user explicitly starts a different context.
- The loopback helper accepts a random per-launch token and recomputes the URL route before
  opening it. A caller cannot label an I2P URL as Tor or vice versa.

These controls prevent accidental browser-state mixing. They do not by themselves provide
Tor Browser fingerprinting resistance or make non-anonymous transports anonymous.

## Relationship To AMPG

AMPG publishes protocol-specific site variants and declares their expected transport,
profile, and isolation mode in fixture manifests. AMPB validates and enforces the browser
side of that contract. AMPG never controls local browser daemon ownership or profile state.
