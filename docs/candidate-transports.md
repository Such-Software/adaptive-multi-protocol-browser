# Candidate Transports

> Status: draft | Updated 2026-07-06 | Applies to: AMPB and AMPG transport planning

Candidate transports are tracked from evaluation through active dry-run support. A
candidate should not become an enabled-by-default route until AMPB has an adapter
contract, fixture behavior, mobile posture, and publishing story for it.

## Selection Rules

- Prefer transports that can open AMPG static output or serve normal web/Gemini content.
- Treat discovery/social protocols as metadata layers, not page transports.
- Treat permanent archives as publishing targets with explicit user warnings.
- Treat resilient overlays separately from anonymity networks.
- Keep mobile constraints visible before a candidate becomes active.

## Current Matrix

Generated candidate metadata lives in
[generated candidate transports](generated/candidate-transports.md).
