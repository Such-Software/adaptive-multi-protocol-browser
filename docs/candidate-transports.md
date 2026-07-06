# Candidate Transports

> Status: draft | Updated 2026-07-06 | Applies to: AMPB and AMPG transport planning

Candidate transports are tracked separately from active adapters. A candidate should not
be routed by default until AMPB has an adapter contract, fixture behavior, mobile posture,
and publishing story for it.

## Selection Rules

- Prefer transports that can open AMPG static output or serve normal web/Gemini content.
- Treat discovery/social protocols as metadata layers, not page transports.
- Treat permanent archives as publishing targets with explicit user warnings.
- Keep mobile constraints visible before a candidate becomes active.

## Current Matrix

Generated candidate metadata lives in
[generated candidate transports](generated/candidate-transports.md).
