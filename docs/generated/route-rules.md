# Generated Route Rules

> Status: generated | Updated by `python3 -m ampbrowser docs generate` | Applies to: AMPB

This file is generated from code. Do not edit it by hand.

| Match | Transport | Profile | Note |
| --- | --- | --- | --- |
| `*.onion` | `tor` | `tor` | route through Tor SOCKS |
| `*.i2p` | `i2p` | `i2p` | route through I2P HTTP proxy |
| `gemini://*` | `gemini` | `gemini` | fetch and render Gemtext |
| `rns://*, lxmf://*, nomad://*` | `reticulum` | `reticulum` | route through Reticulum adapter |
| `http://*, https://*` | `clearnet` | `clearnet` | ordinary web profile |
