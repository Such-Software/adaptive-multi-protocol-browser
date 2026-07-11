# Autodocs

> Status: draft | Updated 2026-07-11 | Applies to: AMPB maintainers

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

Generated files live under `docs/generated/` and must not be edited by hand. They cover
route rules, active transports, browser backend strategy, adapter contracts, candidate
transports, provider sources, and platform capabilities. Browser source trees, object
directories, caches, and artifacts belong under `/tmp/ampb-browser-build` or another
explicit external build workspace, not this repo.

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

The public docs gate checks status headers, internal links, repo-contained local links,
private fixture target names, obvious private-key blocks, common API tokens, and assigned
secret values. Private notes belong under ignored `docs/private/`.
