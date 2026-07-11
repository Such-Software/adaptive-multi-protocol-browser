# Open Flow

> Status: draft | Updated 2026-07-11 | Applies to: AMPB users and implementers

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

By default, `open` output is a dry-run launch spec. Use `--launch` to create the isolated
profile and launch the configured browser runtime when the selected route is already
ready. With `--launch --yes`, AMPB may start an approved managed transport before
launching. Transport setup remains gated by first-use approval and readiness checks.

For a missing transport, `open --launch` does not start anything until approval is
provided. The output includes `setup_prompt_title`, `setup_prompt_body`,
`setup_prompt_approve_label`, and `setup_prompt_approval_command`; native shells should
render those fields as the first-use popup. After approval, launch output includes
`transport_setup_status`, `transport_setup_provider`, `transport_setup_owned`,
`transport_setup_pid`, and `transport_setup_endpoint` so the shell can distinguish an
adopted daemon from an AMPB-owned managed process.

`ampbrowser shell <url>` is the desktop wrapper for this contract. It shows the prompt
through a desktop dialog when possible, falls back to a terminal prompt when needed, and
launches through the same transport runner after approval.

`ampbrowser open <clearnet-url> --broker --launch` creates the single-window desktop entry
profile. Its extension assigns every web tab to a visible clearnet, Tor, or I2P container.
When a top-level URL needs another transport, AMPB starts or adopts it after first-use
consent, creates the destination tab in the matching container at the same position, and
removes the old tab. It never opens a transport-specific browser window. `--route-aware`
remains a compatibility alias for `--broker`.

## Examples

```sh
python3 -m ampbrowser open https://wownero.org/
python3 -m ampbrowser open http://example.b32.i2p/
python3 -m ampbrowser open http://example.b32.i2p/ --yes
python3 -m ampbrowser open http://example.b32.i2p/ --config examples/config.toml
python3 -m ampbrowser open http://example.b32.i2p/ --platform android
python3 -m ampbrowser open https://wownero.org/ --launch
python3 -m ampbrowser open https://ampgateway.site/ --broker --launch
python3 -m ampbrowser open http://example.onion/ --launch
python3 -m ampbrowser open http://example.onion/ --yes --launch
python3 -m ampbrowser shell http://example.onion/
```
