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
7. Continue in a tab carrying the matching transport context.

AMPB has one visible browser window. Each web tab belongs to a named transport container.
A top-level route change replaces that tab in the same window; subresources cannot change
transport. The container controls site-data separation and fail-closed proxy policy.

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

The first implementation should ship an AMPB-owned browser runtime, not attach to the
host system browser. Desktop AMPB should be a bundled Firefox/Gecko-lineage app with
AMPB-owned profiles, transport proxy policy, native transport setup, and health checks.
Android AMPB should use a bundled GeckoView/Fenix/Tor Browser Android-lineage runtime
with visible foreground transport services.

Tor Browser compatibility is the high bar for `.onion` browsing. AMPB must not claim Tor
Browser equivalence until it tracks the relevant Tor Browser hardening, fingerprinting,
proxy, and update behavior. AMPB should not depend on system Firefox, system Chrome, or
the user's default browser.

The release browser requires a reviewed Firefox/Gecko integration. Transport context must
be carried below WebExtensions through origin attributes, channel load information,
connection pools, storage, cache, service workers, and content-process selection.

Generated backend metadata lives in
[generated browser strategy](generated/browser-strategy.md).

The first implementation path is documented in [desktop vertical](desktop-vertical.md).

## Isolation Boundaries

- The prototype isolates cookies and site data with Firefox transport containers.
- Transport runtime state is isolated under AMPB-owned transport directories when AMPB
  manages the daemon.
- A transport context remains sticky: ordinary navigation stays in that context and uses
  its configured proxy until the user explicitly starts a different context.
- The loopback helper accepts a random per-launch token and recomputes the URL route before
  managing it. Web content cannot invoke transport management directly.

Container controls do not separate all Firefox profile state and do not by themselves
provide Tor Browser fingerprinting resistance. Release anonymity claims require the native
Gecko boundary and tracked Tor Browser hardening.

## Relationship To AMPG

AMPG publishes protocol-specific site variants and declares their expected transport,
profile, and isolation mode in fixture manifests. AMPB validates and enforces the browser
side of that contract. AMPG never controls local browser daemon ownership or profile state.
