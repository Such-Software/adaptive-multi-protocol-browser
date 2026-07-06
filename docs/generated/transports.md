# Generated Transports

> Status: generated | Updated by `python3 -m ampbrowser docs generate` | Applies to: AMPB

This file is generated from code. Do not edit it by hand.

| Transport | Adopt Check | Managed State | Profile | Note |
| --- | --- | --- | --- | --- |
| `tor` | SOCKS on 127.0.0.1:9050 | `.ampb/transports/tor` | `tor` | Adopt existing Tor when healthy; otherwise prompt before managed setup. |
| `i2p` | HTTP proxy on 127.0.0.1:4444 | `.ampb/transports/i2p` | `i2p` | Adopt existing i2pd/I2P router when healthy; otherwise prompt before managed setup. |
| `ipfs` | HTTP gateway on 127.0.0.1:8080 | `.ampb/transports/ipfs` | `ipfs` | Adopt existing IPFS gateway when healthy; otherwise prompt before managed setup. |
| `gemini` | built-in renderer available | `.ampb/transports/gemini` | `gemini` | No daemon required for static Gemtext browsing. |
| `reticulum` | RNS tools and configured interfaces | `.ampb/transports/reticulum` | `reticulum` | Adapter planned for resilient/private routing; physical/link-layer setup may require operator config. |
