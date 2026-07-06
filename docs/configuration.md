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
- `gemini://` URLs use the Gemini profile.
- Reticulum-family URLs are routed to the Reticulum adapter once configured.

## Future Config Shape

```toml
[browser]
default_engine = "system"
state_dir = ".ampb"

[transports.tor]
enabled = true
mode = "adopt-or-manage"
socks_endpoint = "127.0.0.1:9050"

[transports.i2p]
enabled = true
mode = "adopt-or-manage"
http_proxy = "127.0.0.1:4444"

[transports.reticulum]
enabled = false
mode = "adopt"

[profiles]
isolate_by_transport = true
```

## Public And Private Files

Public docs describe behavior, configuration, and supported fixtures. Private strategy,
deployment notes, host inventory, generated keys, and local address books belong under
`docs/private/`, which is ignored by git.
