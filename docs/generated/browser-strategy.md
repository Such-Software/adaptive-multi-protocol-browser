# Generated Browser Strategy

> Status: generated | Updated by `python3 -m ampbrowser docs generate` | Applies to: AMPB

This file is generated from code. Do not edit it by hand.

| Backend | Role | Status | Platforms | Launch Mode | Privacy Posture | Note |
| --- | --- | --- | --- | --- | --- | --- |
| `hardened-firefox` | primary web runtime | `planned` | desktop, android | managed profile, policy, and native transport launcher | strong baseline; track Firefox ESR and Tor Browser hardening choices | Default AMPB web runtime before a full browser fork. |
| `tor-browser-compatible` | tor-hardened target | `planned` | desktop, android | adopt, launch, or fork after transport contracts are stable | highest Tor web target; do not claim equivalence until Tor Browser patches are tracked | Path toward real Tor Browser-grade behavior for .onion browsing. |
| `webkit-ios-shell` | ios runtime | `planned` | ios | native shell with embedded transports and isolated web views | platform constrained; avoid clearnet fallback and isolate transport state | Required for App Store-style iOS builds outside special browser-engine entitlements. |
| `gemini-native-viewer` | alternate-web viewer | `planned` | desktop, android, ios | built-in fetch and render path | no web engine or shared browser storage required | Used for Gemini and similar lightweight document transports. |
| `chromium-cef` | prototype fallback | `fallback` | desktop | profile launcher only when Firefox path is blocked | not a Tor Browser privacy baseline | Allowed for experiments, but not the main privacy-browser strategy. |
