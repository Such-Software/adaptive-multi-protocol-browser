# Generated Browser Strategy

> Status: generated | Updated by `python3 -m ampbrowser docs generate` | Applies to: AMPB

This file is generated from code. Do not edit it by hand.

| Backend | Role | Status | Platforms | Launch Mode | Privacy Posture | Note |
| --- | --- | --- | --- | --- | --- | --- |
| `ampb-gecko-desktop` | primary desktop runtime | `planned` | desktop | bundled Firefox/Gecko-lineage app with AMPB-owned profiles and transports | no system browser dependency; track Firefox ESR, Tor Browser, and Mullvad hardening choices | Default desktop runtime; users should not need Firefox installed. |
| `ampb-geckoview-android` | primary android runtime | `planned` | android | bundled GeckoView/Fenix/Tor Browser Android-lineage app with foreground transports | no system browser dependency; app owns profile, proxy policy, and transport lifecycle | Default Android runtime for real mobile AMPB. |
| `ampb-webkit-ios` | ios runtime | `planned` | ios | bundled iOS app shell with WebKit views and embedded transport runtimes | platform constrained; avoid clearnet fallback and isolate transport state | Default iOS path unless alternate browser-engine entitlements become practical. |
| `tor-browser-lineage` | tor-hardened target | `planned` | desktop, android | reuse or track Tor Browser patches after AMPB transport contracts are stable | highest Tor web target; do not claim equivalence until Tor Browser patches are tracked | Path toward real Tor Browser-grade behavior for .onion browsing. |
| `gemini-native-viewer` | alternate-web viewer | `planned` | desktop, android, ios | built-in fetch and render path | no web engine or shared browser storage required | Used for Gemini and similar lightweight document transports. |
