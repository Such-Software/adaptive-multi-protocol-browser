# Architecture

> Status: draft | Updated 2026-07-05 | Applies to: AMPB contributors and integrators

AMPB is a browser orchestration layer for privacy and alternate-network transports. It
keeps the routing, transport management, and profile isolation decisions outside the
browser engine until those contracts are stable.

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
- `ampbrowser.transports`: local readiness checks for Tor, I2P, Reticulum, and Gemini.
- `ampbrowser.plan`: dry-run action planner for browser launches.
- `ampbrowser.docsgen`: generated public documentation from code-owned metadata.

## Browser Strategy

The first implementation should be a launcher and profile manager, not a browser-engine
fork. Tor Browser, Mullvad Browser, Firefox profiles, Chromium profiles, terminal Gemini
clients, and future Reticulum-native viewers can all sit behind the same route and
transport contracts.

The long-term browser can become more integrated once the orchestration surface is boring:
profile isolation is reliable, transport adoption is predictable, and generated fixtures
from AMPG can be opened without manual proxy setup.

## Relationship To AMPG

AMPG publishes protocol-specific site variants. AMPB opens those variants with the right
transport and profile. Wownero is the shared fixture for static publishing, while
interactive targets exercise sessions, dynamic assets, forms, and script policy.
