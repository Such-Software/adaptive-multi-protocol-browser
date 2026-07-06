# Configuration

> Status: draft | Updated 2026-07-05 | Applies to: AMPB users and package maintainers

AMPB should work without a config file for common local setups. Explicit configuration is
for changing defaults, pinning binary paths, choosing managed state directories, and
restricting which transports are allowed.

Transport setup is lazy. AMPB does not install, start, or configure a transport until the
user opens a URL that needs it and approves the first-use prompt.

## Default Behavior

- Clearnet URLs use a clearnet profile.
- `.onion` hosts use Tor through `127.0.0.1:9050` when available.
- `.i2p` hosts use I2P through `127.0.0.1:4444` when available.
- `ipfs://`, `ipns://`, `/ipfs/`, and `/ipns/` addresses use a local IPFS gateway when available.
- `gemini://` URLs use the Gemini profile.
- Reticulum-family URLs use the Reticulum adapter for resilient/private routing once configured.

## Config File

By default AMPB reads `.ampb/config.toml` from the current working directory. Commands
that make launch decisions also accept `--config <path>`.

Example configs live under `examples/`.

```toml
[browser]
default_engine = "system"
state_dir = ".ampb"

[transports.tor]
enabled = true
mode = "adopt-or-prompt-manage"
socks_endpoint = "127.0.0.1:9050"

[transports.i2p]
enabled = true
mode = "adopt-or-prompt-manage"
http_proxy = "127.0.0.1:4444"

[transports.ipfs]
enabled = true
mode = "adopt-or-prompt-manage"
gateway = "127.0.0.1:8080"

[transports.reticulum]
enabled = false
mode = "adopt"

[profiles]
isolate_by_transport = true
```

Supported transport modes:

- `disabled`: do not open URLs that require this transport.
- `adopt`: use the transport only if it is already running.
- `adopt-or-prompt-manage`: adopt a running transport, otherwise show a first-use prompt
  before managed setup.

## Public And Private Files

Public docs describe behavior, configuration, and supported fixtures. Private strategy,
deployment notes, host inventory, generated keys, and local address books belong under
`docs/private/`, which is ignored by git.
