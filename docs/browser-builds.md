# Browser Builds

> Status: draft | Updated 2026-07-07 | Applies to: AMPB desktop and mobile builders

AMPB browser builds must keep source checkouts, object directories, toolchain caches, and
temporary artifacts outside this repository. The default local workspace is
`/tmp/ampb-browser-build`.

## Runtime Targets

- Desktop: bundled Firefox/Gecko-lineage AMPB app.
- Android: bundled GeckoView/Fenix/Tor Browser Android-lineage AMPB app.
- iOS: AMPB-owned iOS shell with platform WebKit constraints and embedded transports.
- Tor hardening: track Tor Browser behavior before claiming Tor Browser equivalence.

## Workspace

Create a local build workspace:

```sh
sh tools/browser-build-workspace.sh
```

Override the root when needed:

```sh
AMPB_BROWSER_BUILD_ROOT=/tmp/ampb-browser-build sh tools/browser-build-workspace.sh
```

The script creates:

- `/tmp/ampb-browser-build/src`
- `/tmp/ampb-browser-build/obj`
- `/tmp/ampb-browser-build/cache`
- `/tmp/ampb-browser-build/artifacts`
- `/tmp/ampb-browser-build/logs`

## Repo Rule

Keep only repeatable scripts, clean docs, and small AMPB source changes in this repo.
Do not commit Firefox source trees, GeckoView checkouts, Tor Browser build trees, browser
object directories, SDK downloads, signing material, generated profiles, release artifacts,
or machine-local notes.

## Rebuild Notes

Public rebuild docs should be general and credential-free. Private signing, release,
account, and machine inventory notes belong outside public docs.
