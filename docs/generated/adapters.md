# Generated Transport Adapters

> Status: generated | Updated by `python3 -m ampbrowser docs generate` | Applies to: AMPB

This file is generated from code. Do not edit it by hand.

| Adapter | Endpoint | Adopt Check | Install Strategy | Start Strategy | Stop Policy | Note |
| --- | --- | --- | --- | --- | --- | --- |
| `tor` | `socks5://127.0.0.1:9050` | SOCKS on 127.0.0.1:9050 | install Tor provider | start managed Tor daemon | stop only AMPB-owned Tor daemon | Tor SOCKS proxy |
| `i2p` | `http://127.0.0.1:4444` | HTTP proxy on 127.0.0.1:4444 | install I2P provider | start managed I2P router | stop only AMPB-owned I2P router | I2P HTTP proxy |
| `reticulum` | `rns://local` | RNS tools and configured interfaces | install Reticulum provider | start configured Reticulum interface | stop only AMPB-owned Reticulum process | Reticulum adapter is planned; interface readiness needs explicit config |
| `gemini` | `builtin://gemtext-renderer` | built-in renderer available | unsupported | use built-in Gemtext fetch/render path | no daemon to stop | Built-in Gemtext fetch/render path |
