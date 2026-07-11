# Transport Broker

> Status: draft | Updated 2026-07-11 | Applies to: AMPB desktop users and implementers

The transport broker is AMPB's clearnet entry profile. It gives users one place to begin
without combining clearnet, Tor, and I2P browser storage or proxy policy.

## Handoff

1. The broker profile begins a top-level navigation.
2. Its extension recognizes `.onion` or `.i2p` and cancels the request.
3. A token-gated loopback helper independently routes the URL.
4. If needed, AMPB asks for first-use consent and starts or adopts the transport.
5. AMPB opens the URL in `.ampb/profiles/tor` or `.ampb/profiles/i2p` with that profile's
   proxy policy.
6. The broker tab reports that the route opened in an isolated context.

AMPB records the process it launches for each exact profile. Later handoffs reuse only a
live process recorded for that profile; otherwise AMPB launches a new isolated process.

The helper rejects a handoff when the supplied transport does not match the URL. It is
tied to the broker browser process and stops when that process exits.

Subresources, frames, and background requests to alternate-network hosts are blocked in
the clearnet broker and are not converted into handoffs. Only top-level navigation can
open another transport context.

## Boundaries

The broker separates cookies, cache, history, service workers, and other profile storage
by transport. AMPB-managed daemon state is separately stored under
`.ampb/transports/<transport>`.

Transport isolation is not an anonymity claim. Tor browsing still requires Tor Browser
hardening and update parity before AMPB can claim equivalent fingerprinting resistance.
I2P and Reticulum have different threat models and must be described on their own terms.

## Command

```sh
python3 -m ampbrowser open https://ampgateway.site/ --broker --launch
```

`--route-aware` is retained as a compatibility alias for `--broker`.
