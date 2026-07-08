# Transport Management

> Status: draft | Updated 2026-07-08 | Applies to: AMPB transport adapters

Transport management follows one rule: use what is already healthy, and manage missing
transports only after the user opens a URL that needs them and approves setup.

`ampbrowser open` emits a dry-run launch spec by default. The spec includes the selected
profile, proxy endpoint, browser runtime path, generated profile prefs path, required
setup steps, and whether user consent is still needed. With `--launch`, AMPB creates the
profile and starts the bundled browser only when the selected route is already ready.
With `--launch --yes`, AMPB can start configured Tor and I2P providers with AMPB-owned
state before launching. Transport policy comes from `.ampb/config.toml` or an explicit
`--config` path.

`ampbrowser transport start|status|stop <name>` exposes the same ownership model without
launching a browser. It records only AMPB-owned processes and refuses to stop adopted
user or system daemons.

Route-aware desktop launches add a local helper process for in-browser setup prompts. The
helper accepts token-gated loopback requests from the AMPB profile extension, reports
transport status, and starts only supported AMPB-managed transports. It does not expose a
public network listener or manage adopted daemons. The helper watches the browser process
and exits when that isolated browser exits.

## Lifecycle

1. Inspect known local endpoints.
2. Adopt running transports that match the selected URL.
3. For missing transports, show a prompt that names what will be installed or started.
4. Resolve a configured binary and state directory only after consent.
5. Start the daemon, library runtime, or foreground service with AMPB-owned state.
6. Wait for the health endpoint.
7. Launch the browser profile only after the transport is ready.
8. Stop only AMPB-owned daemons.

## Ownership

AMPB never stops a daemon it did not start. Adopted transports remain owned by the user,
system service, or package manager that launched them.

Managed transports store runtime state under `.ampb/transports/<name>` by default. Keys,
leases, tunnels, and daemon logs in that tree are local state and must not be committed.
AMPB records owned process metadata in `.ampb/transports/<name>/ampb-owned.json`.

## Current Adapters

- Tor: detect SOCKS on `127.0.0.1:9050`; managed start supports Arti, configured `tor`,
  and system `tor` providers with AMPB-owned state.
- I2P: detect HTTP proxy on `127.0.0.1:4444`; managed start supports configured or system
  `i2pd` providers with AMPB-owned state.
- IPFS: detect HTTP gateway on `127.0.0.1:8080`; managed gateway start planned.
- Gemini: built-in route and render path; no daemon required for static browsing.
- Reticulum: resilient/private route contract exists; adapter and readiness model are planned.

Generated transport metadata lives in [generated transports](generated/transports.md).
Adapter ownership and setup contracts live in [generated adapters](generated/adapters.md).
