# Generated Provider Sources

> Status: generated | Updated by `python3 -m ampbrowser docs generate` | Applies to: AMPB

This file is generated from code. Do not edit it by hand.


## Source Types

| Source | Discovery | Lifecycle | Platforms | Note |
| --- | --- | --- | --- | --- |
| `configured` | explicit config or environment variable | operator override; AMPB owns profile policy but not the binary provenance | desktop, android, ios | Used for development, custom bundles, and reviewed advanced installs. |
| `bundled-sidecar` | provider binary shipped with AMPB or the build workspace | AMPB-owned process and isolated state | desktop, android | Default desktop target for Tor, I2P, IPFS, Reticulum, and similar daemon-style transports. |
| `embedded-library` | transport library linked into the app process | AMPB-owned foreground session and app-private state | android, ios | Preferred mobile shape when platform policy makes sidecar daemons awkward. |
| `system-adopted` | healthy local proxy or service already running | operator-owned service; AMPB only routes browser traffic to it | desktop, android | Keeps power users and existing deployments working without duplicate daemons. |
| `system-package` | known package manager install such as brew, apt, pkg, or platform provider | installed only after user consent, then run with AMPB-owned state | desktop, android | Fallback when the app did not ship that provider yet. |
| `builtin-renderer` | browser-native renderer or fetch path | AMPB-owned code path with no external daemon | desktop, android, ios | Used for Gemini and other lightweight document transports. |

## Transport Providers

| Transport | Provider | Sources | Endpoint | Status | Note |
| --- | --- | --- | --- | --- | --- |
| `tor` | `arti/tor` | `configured`, `bundled-sidecar`, `embedded-library`, `system-adopted`, `system-package` | `socks5://127.0.0.1:9050` | `active` | Desktop uses managed Arti/Tor sidecars today; mobile should prefer embedded or app-owned foreground providers. |
| `i2p` | `i2pd/i2p-router` | `configured`, `bundled-sidecar`, `embedded-library`, `system-adopted`, `system-package` | `http://127.0.0.1:4444` | `active` | Desktop can adopt or manage i2pd; mobile provider packaging is planned behind the same contract. |
| `gemini` | `gemini-native-viewer` | `builtin-renderer` | `builtin://gemtext-renderer` | `planned` | No daemon is required once the built-in fetch/render path exists. |
| `ipfs` | `kubo/ipfs` | `configured`, `bundled-sidecar`, `system-adopted`, `system-package` | `http://127.0.0.1:8080` | `planned` | Content-addressed browsing uses the same provider lifecycle without treating IPFS as anonymity. |
| `reticulum` | `rnsd/rnstatus` | `configured`, `bundled-sidecar`, `system-adopted`, `system-package` | `rns://local` | `planned` | Reticulum browsing may still need operator-owned physical or link-layer interface setup. |
