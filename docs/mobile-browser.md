# Mobile Browser

> Status: draft | Updated 2026-07-07 | Applies to: AMPB mobile shells

Mobile is a first-class AMPB target. The core router, policy model, consent flow, profile
isolation, and fixture checks should stay shared across desktop, Android, and iOS. Native
mobile shells should implement only the platform-specific browser and transport pieces.

## Android

Android is the primary mobile target for full AMPB browsing. Tor, I2P, IPFS, and
Reticulum adapters should run only after a URL selects that transport and the user
approves setup. Managed adapters must use visible, stoppable foreground services and
app-owned state. Tor should prefer an Arti/Tor runtime path when the native shell can
support it cleanly.

## iOS

iOS is a supported design target, but transport management is constrained. AMPB should
assume foreground-only sessions for managed transports unless a reviewed platform
capability proves otherwise. The iOS shell should still share routing, policy, consent,
fixture, Gemini, IPFS gateway, and clearnet behavior with the rest of AMPB.

Tor on iOS should be modeled as an embedded Arti session, not a global daemon install.
The first vertical should prove foreground `.onion` browsing through an app-owned Arti
runtime and a browser networking bridge before promising background operation or a
system-wide proxy.

## Capability Matrix

Generated platform capability metadata lives in
[generated platform capabilities](generated/platform-capabilities.md).
