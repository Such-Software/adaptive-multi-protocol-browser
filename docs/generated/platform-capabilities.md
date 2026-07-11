# Generated Platform Capabilities

> Status: generated | Updated by `python3 -m ampbrowser docs generate` | Applies to: AMPB

This file is generated from code. Do not edit it by hand.

| Transport | Platform | Browse | Adopt | Manage | Install | Note |
| --- | --- | --- | --- | --- | --- | --- |
| `clearnet` | `desktop` | `ready` | `ready` | `unsupported` | `unsupported` | Use one bundled AMPB Gecko window with isolated transport contexts. |
| `clearnet` | `android` | `ready` | `ready` | `unsupported` | `unsupported` | Use one bundled GeckoView app with isolated transport sessions. |
| `clearnet` | `ios` | `ready` | `ready` | `unsupported` | `unsupported` | Use bundled AMPB iOS shell with platform WebKit constraints. |
| `tor` | `desktop` | `ready` | `ready` | `planned` | `planned` | Adopt local Tor or prompt before managed Arti SOCKS setup. |
| `tor` | `android` | `planned` | `planned` | `planned` | `planned` | Use an app-owned foreground service; prefer Arti/Tor runtime integration where available. |
| `tor` | `ios` | `foreground-only` | `planned` | `foreground-only` | `bundled` | Use foreground embedded Arti sessions; do not assume background service or global proxy. |
| `i2p` | `desktop` | `ready` | `ready` | `planned` | `planned` | Adopt local I2P proxy or prompt before managed desktop daemon setup. |
| `i2p` | `android` | `planned` | `planned` | `planned` | `planned` | Use an app-owned foreground service or compatible installed I2P provider. |
| `i2p` | `ios` | `constrained` | `planned` | `foreground-only` | `constrained` | Treat iOS I2P support as foreground-only until native adapter constraints are proven. |
| `ipfs` | `desktop` | `ready` | `ready` | `planned` | `planned` | Adopt local IPFS gateway or prompt before managed gateway setup. |
| `ipfs` | `android` | `planned` | `planned` | `planned` | `planned` | Use gateway-first IPFS browsing; embedded node support needs adapter proof. |
| `ipfs` | `ios` | `constrained` | `planned` | `foreground-only` | `constrained` | Use gateway-first IPFS browsing; embedded node support is constrained. |
| `gemini` | `desktop` | `ready` | `ready` | `ready` | `unsupported` | Built-in fetch/render path can be shared by desktop shell. |
| `gemini` | `android` | `ready` | `ready` | `ready` | `unsupported` | Built-in fetch/render path can be shared by Android shell. |
| `gemini` | `ios` | `ready` | `ready` | `ready` | `unsupported` | Built-in fetch/render path can be shared by iOS shell. |
| `reticulum` | `desktop` | `planned` | `planned` | `planned` | `planned` | Resilient/private networking adapter and interface checks are planned. |
| `reticulum` | `android` | `planned` | `planned` | `planned` | `planned` | Mobile resilient-network adapter should use explicit foreground service consent. |
| `reticulum` | `ios` | `constrained` | `planned` | `foreground-only` | `constrained` | Do not assume background Reticulum operation on iOS. |
| `unknown` | `desktop` | `unsupported` | `unsupported` | `unsupported` | `unsupported` | No platform route is available. |
| `unknown` | `android` | `unsupported` | `unsupported` | `unsupported` | `unsupported` | No platform route is available. |
| `unknown` | `ios` | `unsupported` | `unsupported` | `unsupported` | `unsupported` | No platform route is available. |
