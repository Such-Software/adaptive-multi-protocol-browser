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

## Desktop Build Probe

Desktop is the first browser proof. The probe uses the current Gecko checkout and writes
its mozconfig, object directory, caches, and logs under `/tmp`.

Print the desktop build entrypoint help:

```sh
sh tools/browser-desktop-build-probe.sh
```

Run the first desktop configure probe:

```sh
AMPB_DESKTOP_BUILD_PROBE_MODE=configure sh tools/browser-desktop-build-probe.sh
```

Run the first desktop source build:

```sh
AMPB_DESKTOP_BUILD_PROBE_MODE=build sh tools/browser-desktop-build-probe.sh
```

The default `source` flavor is the verified desktop path. Use
`AMPB_DESKTOP_BUILD_FLAVOR=artifact` only as a faster optional probe; it depends on
Mozilla artifact availability for the selected checkout.

The probe writes:

- `/tmp/ampb-browser-build/mozconfigs/desktop-source.mozconfig`
- `/tmp/ampb-browser-build/obj/gecko-desktop-source`
- `/tmp/ampb-browser-build/logs/gecko-desktop-source-mach-help.log`
- `/tmp/ampb-browser-build/logs/gecko-desktop-source-mach-configure.log`
- `/tmp/ampb-browser-build/logs/gecko-desktop-source-mach-build.log`

A successful source build produces a bundled app at
`/tmp/ampb-browser-build/obj/gecko-desktop-source/dist/Nightly.app`.

Configure and build modes may install Mozilla build Python helpers such as `zstandard`
into mach virtualenvs under `/tmp/ampb-browser-build/cache/mozbuild`.

## Tor Provider Probe

Build a local Arti provider for managed Tor startup:

```sh
sh tools/browser-tor-provider-build.sh
```

The provider script keeps Cargo output and the installed Arti binary under the external
workspace:

- `/tmp/ampb-browser-build/providers/arti/bin/arti`
- `/tmp/ampb-browser-build/logs/arti-cargo-install.log`

`ampbrowser open <onion-url> --yes --launch` will prefer this local Arti provider, then
`AMPB_ARTI_BIN`, `AMPB_TOR_BIN`, configured `transports.tor.binary_path`, and finally a
system `tor` binary if one is present.

## Source Plan

Print the canonical source targets and paths:

```sh
sh tools/browser-source-plan.sh
```

Clone or refresh the source trees under `/tmp`:

```sh
sh tools/browser-source-sync.sh
```

Report checked-out source revisions:

```sh
sh tools/browser-source-report.sh
```

Defaults:

- Current Gecko / Firefox Android source: `https://github.com/mozilla/gecko-dev.git`
- Tor Browser build recipes: `https://gitlab.torproject.org/tpo/applications/tor-browser-build.git`
- Legacy archived Android layout reference: `https://github.com/mozilla-mobile/firefox-android.git`

Override repositories for experiments without editing the repo:

```sh
AMPB_GECKO_REPO=https://github.com/mozilla/gecko-dev.git sh tools/browser-source-sync.sh
```

The legacy Firefox Android repository is archived and should not be treated as the current
source of truth. Clone it only when comparing older `fenix`, `focus-android`, or
`android-components` layout:

```sh
AMPB_INCLUDE_LEGACY_FIREFOX_ANDROID=1 sh tools/browser-source-sync.sh
```

## Android Build Probe

Android remains a first-class target, but it follows the desktop proof. Run the first
Android build-discovery command from the `/tmp` checkout while keeping
Gradle, pip, Python bytecode, and Mozilla build state in `/tmp`:

```sh
sh tools/browser-android-build-probe.sh
```

The probe writes its log to
`/tmp/ampb-browser-build/logs/gecko-android-mach-probe.log`.

This first probe intentionally asks `mach` for Android build help instead of compiling the
world. It verifies that the current Gecko checkout, `mach`, Python virtualenv state, and
Android build command entry point can initialize from `/tmp` before a longer bootstrap or
compile run.

## Repo Rule

Keep only repeatable scripts, clean docs, and small AMPB source changes in this repo.
Do not commit Firefox source trees, GeckoView checkouts, Tor Browser build trees, browser
object directories, SDK downloads, signing material, generated profiles, release artifacts,
or machine-local notes.

## Rebuild Notes

Public rebuild docs should be general and credential-free. Private signing, release,
account, and machine inventory notes belong outside public docs.
