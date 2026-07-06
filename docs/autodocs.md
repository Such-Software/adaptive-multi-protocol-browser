# Autodocs

> Status: draft | Updated 2026-07-05 | Applies to: AMPB maintainers

Public docs should stay concise and current. Code-owned behavior is documented from code,
while manual docs explain stable concepts and operator-facing choices.

## Generated Docs

Run:

```sh
python3 -m ampbrowser docs generate
```

Check for drift:

```sh
python3 -m ampbrowser docs generate --check
```

Generated files live under `docs/generated/` and must not be edited by hand.

## Manual Docs

Manual public docs must include a status header near the top and should avoid strategy
notes, checkpointing, timelines, private addresses, local hostnames, credentials, and
deployment inventory.

Private notes belong in `docs/private/`. That directory is ignored and should remain
absent from commits.

## Link And Header Check

Run:

```sh
python3 tools/docs_check.py
```
