# Fixture Manifests

> Status: draft | Updated 2026-07-06 | Applies to: AMPB and AMPG compatibility checks

AMPB can check AMPG fixture manifests without contacting any network. The check confirms
that each generated fixture URL routes to the expected AMPB transport and profile.

## Command

```sh
python3 -m ampbrowser fixture check ../adaptive-multi-protocol-gateway/dist/wownero/ampg-fixture-manifest.json
```

The command exits non-zero when any fixture route does not match the manifest.

## Scope

Fixture checks validate route selection only. They do not verify daemon health, hidden
service reachability, IPFS pinning, TLS, or content freshness.

The manifest must not contain private deployment notes, service keys, credentials, or
host inventory.
