# Test Fixtures

> Status: draft | Updated 2026-07-11 | Applies to: AMPB and AMPG compatibility testing

Fixtures should cover static sites, protocol-specific publishing, and interactive web
apps without exposing private deployment notes.

## Primary Fixture

Wownero is the first shared fixture between AMPG and AMPB. It exercises ordinary
clearnet pages, Tor and I2P HTML variants, Gemini output, static assets, and semantic
HTML improvements that improve alternate renderers.

## Interactive Fixtures

Stretch fixtures cover dynamic behavior: sessions, forms, asset policy, script policy,
tenant routing, payments, job-style workflows, and transport-specific degradation.

## Fixture Requirements

- Every fixture has a public description of what behavior it exercises.
- Private addresses, tunnel keys, host inventory, and credentials stay out of public docs.
- Browser checks prefer dry-run plans before live launch.
- Static output from AMPG should be openable by AMPB without manual proxy setup.
- AMPG fixture manifests should pass `ampbrowser fixture check`.
