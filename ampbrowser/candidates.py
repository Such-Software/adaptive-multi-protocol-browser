from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateTransport:
    name: str
    role: str
    status: str
    route_examples: tuple[str, ...]
    browser_fit: str
    publisher_fit: str
    mobile_fit: str
    source: str
    note: str


CANDIDATE_TRANSPORTS = (
    CandidateTransport(
        name="ipfs",
        role="content-addressed web",
        status="active-dry-run",
        route_examples=("ipfs://<cid>", "/ipfs/<cid>", "ipns://<name>"),
        browser_fit="native fetch or local gateway",
        publisher_fit="static site export and pinning",
        mobile_fit="gateway first; embedded node later",
        source="https://docs.ipfs.tech/concepts/what-is-ipfs/",
        note="Strong fit for AMPG static output; not an anonymity layer by itself.",
    ),
    CandidateTransport(
        name="yggdrasil",
        role="encrypted IPv6 overlay",
        status="next-evaluate",
        route_examples=("http://[0200::]/", "https://<yggdrasil-host>/"),
        browser_fit="ordinary HTTP over overlay IPv6",
        publisher_fit="serve normal HTTP/Gemini over overlay address",
        mobile_fit="cross-platform, but mobile lifecycle needs adapter proof",
        source="https://yggdrasil-network.github.io/",
        note="Good fit for old-phone nodes and local/community mesh scenarios.",
    ),
    CandidateTransport(
        name="lokinet",
        role="low-latency onion-routed overlay",
        status="evaluate",
        route_examples=("http://<name>.loki/", "https://<name>.loki/"),
        browser_fit="ordinary IP traffic over overlay",
        publisher_fit="SNApp-style hidden service publishing",
        mobile_fit="Android likely first; iOS constrained",
        source="https://docs.oxen.io/oxen-docs/products-built-on-oxen/lokinet",
        note="Interesting Tor/I2P-adjacent candidate; depends on project health and packaging.",
    ),
    CandidateTransport(
        name="hyphanet",
        role="privacy-preserving publishing datastore",
        status="explore",
        route_examples=("USK@...", "CHK@...", "SSK@..."),
        browser_fit="local proxy/freesite viewer",
        publisher_fit="censorship-resistant site publishing",
        mobile_fit="possible on Android; iOS unlikely for full node",
        source="https://www.hyphanet.org/",
        note="Strong ideological fit; UX and key/address model need careful design.",
    ),
    CandidateTransport(
        name="gnunet",
        role="privacy-preserving network stack",
        status="explore",
        route_examples=("gnunet://...", "gns://..."),
        browser_fit="adapter required",
        publisher_fit="future decentralized naming and publishing",
        mobile_fit="research first",
        source="https://www.gnunet.org/en/about.html",
        note="Powerful but early-alpha per upstream; keep as research track.",
    ),
    CandidateTransport(
        name="arweave",
        role="permanent web archive",
        status="publisher-target",
        route_examples=("ar://<txid>", "https://arweave.net/<txid>"),
        browser_fit="gateway or HTTP API fetch",
        publisher_fit="permanent static snapshots",
        mobile_fit="publisher/export flow, not daemon-first",
        source="https://docs.arweave.org/developers/arweave-node-server/http-api",
        note="Great archival target; permanence has moderation and privacy implications.",
    ),
    CandidateTransport(
        name="nostr",
        role="signed event relay network",
        status="discovery-layer",
        route_examples=("nostr:<event>", "nprofile...", "nevent..."),
        browser_fit="discovery, comments, mirrors, address announcements",
        publisher_fit="announce transport addresses and signed updates",
        mobile_fit="good mobile fit; relay selection and spam controls matter",
        source="https://github.com/nostr-protocol/nips/blob/master/01.md",
        note="Not a web-page transport; useful as signed metadata and social distribution.",
    ),
)
