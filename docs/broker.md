# Transport Contexts

> Status: draft | Updated 2026-07-11 | Applies to: AMPB desktop users and implementers

AMPB presents clearnet, Tor, and I2P in one browser window. Every web tab has a visible
transport container. Changing transports replaces the tab in the same position and window;
it never opens a transport-specific browser window.

## Tab Flow

1. AMPB routes a top-level URL before it loads.
2. The current tab continues when its transport context is compatible.
3. A different transport is started or adopted only after first-use consent.
4. AMPB creates the destination tab in the matching container and removes the old tab.
5. Firefox displays the container name and color on the tab and address bar.

Subresources cannot switch transports. A mismatched image, frame, script, WebSocket, or
background request is blocked. Tor tabs may reach clearnet destinations through Tor. I2P
tabs are restricted to I2P destinations unless the user explicitly approves a switch to
clearnet.

## Network Policy

- Clearnet containers use direct networking.
- Tor containers use SOCKS with proxy-side DNS and a stable first-party isolation token.
- I2P containers use the local I2P HTTP proxy and fail closed for non-I2P destinations.
- No transport has a direct fallback when its proxy is unavailable.
- Speculative connections, prefetching, WebRTC, HTTP/3, and browser DNS-over-HTTPS are
  disabled in the container prototype.

The token-gated loopback helper can inspect, start, or adopt transports. It cannot open
browser windows or choose a tab's route.

## Security Boundary

Firefox containers separate cookies, logins, and site data, but they do not separate every
piece of profile state. The one-window WebExtension implementation is therefore a UX and
routing prototype, not a claim of Tor Browser anonymity equivalence.

The release-grade boundary belongs in Gecko. A native `TransportContextId` carried through
origin attributes and channel load information must partition storage, cache, permissions,
connections, DNS, service workers, and content processes while applying fail-closed network
policy below extension code.

## Command

```sh
python3 -m ampbrowser open https://ampgateway.site/ --broker --launch
```

`--route-aware` is retained as a compatibility alias for `--broker`.
