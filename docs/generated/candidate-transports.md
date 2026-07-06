# Generated Candidate Transports

> Status: generated | Updated by `python3 -m ampbrowser docs generate` | Applies to: AMPB

This file is generated from code. Do not edit it by hand.

| Candidate | Role | Status | Routes | Browser Fit | Publisher Fit | Mobile Fit | Source | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ipfs` | content-addressed web | `next-evaluate` | `ipfs://<cid>`, `/ipfs/<cid>`, `ipns://<name>` | native fetch or local gateway | static site export and pinning | gateway first; embedded node later | [source](https://docs.ipfs.tech/concepts/what-is-ipfs/) | Strong fit for AMPG static output; not an anonymity layer by itself. |
| `yggdrasil` | encrypted IPv6 overlay | `next-evaluate` | `http://[0200::]/`, `https://<yggdrasil-host>/` | ordinary HTTP over overlay IPv6 | serve normal HTTP/Gemini over overlay address | cross-platform, but mobile lifecycle needs adapter proof | [source](https://yggdrasil-network.github.io/) | Good fit for old-phone nodes and local/community mesh scenarios. |
| `lokinet` | low-latency onion-routed overlay | `evaluate` | `http://<name>.loki/`, `https://<name>.loki/` | ordinary IP traffic over overlay | SNApp-style hidden service publishing | Android likely first; iOS constrained | [source](https://docs.oxen.io/oxen-docs/products-built-on-oxen/lokinet) | Interesting Tor/I2P-adjacent candidate; depends on project health and packaging. |
| `hyphanet` | privacy-preserving publishing datastore | `explore` | `USK@...`, `CHK@...`, `SSK@...` | local proxy/freesite viewer | censorship-resistant site publishing | possible on Android; iOS unlikely for full node | [source](https://www.hyphanet.org/) | Strong ideological fit; UX and key/address model need careful design. |
| `gnunet` | privacy-preserving network stack | `explore` | `gnunet://...`, `gns://...` | adapter required | future decentralized naming and publishing | research first | [source](https://www.gnunet.org/en/about.html) | Powerful but early-alpha per upstream; keep as research track. |
| `arweave` | permanent web archive | `publisher-target` | `ar://<txid>`, `https://arweave.net/<txid>` | gateway or HTTP API fetch | permanent static snapshots | publisher/export flow, not daemon-first | [source](https://docs.arweave.org/developers/arweave-node-server/http-api) | Great archival target; permanence has moderation and privacy implications. |
| `nostr` | signed event relay network | `discovery-layer` | `nostr:<event>`, `nprofile...`, `nevent...` | discovery, comments, mirrors, address announcements | announce transport addresses and signed updates | good mobile fit; relay selection and spam controls matter | [source](https://github.com/nostr-protocol/nips/blob/master/01.md) | Not a web-page transport; useful as signed metadata and social distribution. |
