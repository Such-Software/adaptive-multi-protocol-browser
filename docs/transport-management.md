# Transport Management

> Status: draft | Updated 2026-07-05 | Applies to: AMPB transport adapters

Transport management follows one rule: use what is already healthy, and manage missing
transports only after the user opens a URL that needs them and approves setup.

`ampbrowser open` currently emits a dry-run launch spec. The spec includes the selected
profile, proxy endpoint, required setup steps, and whether user consent is still needed.

## Lifecycle

1. Inspect known local endpoints.
2. Adopt running transports that match the selected URL.
3. For missing transports, show a prompt that names what will be installed or started.
4. Resolve a configured binary and state directory only after consent.
5. Start the daemon with AMPB-owned state.
6. Wait for the health endpoint.
7. Launch the browser profile only after the transport is ready.
8. Stop only AMPB-owned daemons.

## Ownership

AMPB never stops a daemon it did not start. Adopted transports remain owned by the user,
system service, or package manager that launched them.

Managed transports store runtime state under `.ampb/transports/<name>` by default. Keys,
leases, tunnels, and daemon logs in that tree are local state and must not be committed.

## Current Adapters

- Tor: detect SOCKS on `127.0.0.1:9050`; managed start planned.
- I2P: detect HTTP proxy on `127.0.0.1:4444`; managed start planned.
- Gemini: built-in route and render path; no daemon required for static browsing.
- Reticulum: route contract exists; adapter and readiness model are planned.

Generated transport metadata lives in [generated transports](generated/transports.md).
