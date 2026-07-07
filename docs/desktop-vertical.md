# Desktop Vertical

> Status: draft | Updated 2026-07-07 | Applies to: AMPB desktop builders

The first AMPB browser proof is desktop-first with mobile constraints kept in view. The
vertical is a bundled Gecko desktop runtime, AMPB-owned profile state, and a managed Tor
runtime for `.onion` browsing. Android and iOS follow the same routing and transport
contracts after the desktop path is proven.

## Build Path

Use the external build workspace:

```sh
sh tools/browser-build-workspace.sh
sh tools/browser-source-sync.sh
AMPB_DESKTOP_BUILD_PROBE_MODE=configure sh tools/browser-desktop-build-probe.sh
```

The desktop probe keeps Gecko source, object files, downloaded toolchains, Python
virtualenvs, pip cache, and logs under `/tmp/ampb-browser-build`.

## Transport Path

The first transport target is Tor through an AMPB-owned Arti/Tor runtime. The desktop
vertical is not complete until AMPB can start the runtime, verify the SOCKS endpoint, and
launch the bundled browser profile without clearnet fallback. I2P and Reticulum use the
same route, consent, state, and health-check model after Tor works.
