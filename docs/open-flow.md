# Open Flow

> Status: draft | Updated 2026-07-05 | Applies to: AMPB users and implementers

`ampbrowser open` prepares a safe launch plan for one URL. It routes the URL, checks only
the selected transport, and reports whether the browser can open immediately or needs a
first-use setup prompt.

## Consent Model

AMPB does not install or start Tor, I2P, IPFS, Reticulum, or other optional transports when the
application starts. Setup is lazy:

1. The user opens a URL.
2. AMPB selects the required transport.
3. If the transport is already running, AMPB adopts it.
4. If the transport is missing, AMPB shows a prompt naming what will be installed or started.
5. AMPB proceeds only after approval.

Current `open` output is a dry-run launch spec. It is intentionally side-effect free while
the transport adapters and browser launcher are being stabilized.

## Examples

```sh
python3 -m ampbrowser open https://wownero.org/
python3 -m ampbrowser open http://example.b32.i2p/
python3 -m ampbrowser open http://example.b32.i2p/ --yes
python3 -m ampbrowser open http://example.b32.i2p/ --config examples/config.toml
python3 -m ampbrowser open http://example.b32.i2p/ --platform android
```
