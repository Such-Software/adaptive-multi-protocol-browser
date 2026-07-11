# Fixture Manifests

> Status: draft | Updated 2026-07-11 | Applies to: AMPB and AMPG compatibility checks

AMPB can check AMPG fixture manifests without contacting any network. The check confirms
that each generated fixture URL routes to the expected AMPB transport context, uses
the declared transport-context isolation contract, and fits that transport's interaction
policy.

`ampg.fixture-manifest.v2` uses `checks.context` for the logical browser context. AMPB can
still read v1 manifests for route compatibility, but v2 is required for the current
one-window isolation contract.

Route-expanded fixtures may include `route.match` and `route.fixture_path`, which identify
the route group that produced the fixture.

## Command

```sh
python3 -m ampbrowser fixture check ../adaptive-multi-protocol-gateway/dist/wownero/ampg-fixture-manifest.json
```

The command exits non-zero when any fixture route or interaction policy does not match the
manifest.

## Scope

Fixture checks validate route selection, context isolation expectations, and declared
interaction policy only. They do not verify engine-level partitioning, daemon health, hidden
service reachability, IPFS pinning, TLS, or content freshness.

The manifest must not contain private deployment notes, service keys, credentials, or
host inventory.
