# Mobile Browser

> Status: draft | Updated 2026-07-06 | Applies to: AMPB mobile shells

Mobile is a first-class AMPB target. The core router, policy model, consent flow, profile
isolation, and fixture checks should stay shared across desktop, Android, and iOS. Native
mobile shells should implement only the platform-specific browser and transport pieces.

## Android

Android is the primary mobile target for full AMPB browsing. Tor, I2P, and Reticulum
adapters should run only after a URL selects that transport and the user approves setup.
Managed adapters must use visible, stoppable foreground services and app-owned state.

## iOS

iOS is a supported design target, but transport management is constrained. AMPB should
assume foreground-only sessions unless a reviewed platform capability proves otherwise.
The iOS shell should still share routing, policy, consent, fixture, Gemini, and clearnet
behavior with the rest of AMPB.

## Capability Matrix

Generated platform capability metadata lives in
[generated platform capabilities](generated/platform-capabilities.md).
