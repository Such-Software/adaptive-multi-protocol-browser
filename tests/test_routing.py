from __future__ import annotations

import unittest

from ampbrowser.routing import route_url


class RouteUrlTest(unittest.TestCase):
    def test_defaults_plain_host_to_https_clearnet(self) -> None:
        route = route_url("wownero.org")

        self.assertEqual("https://wownero.org", route.normalized)
        self.assertEqual("clearnet", route.transport)
        self.assertEqual("clearnet", route.profile)

    def test_routes_onion_hosts_to_tor(self) -> None:
        route = route_url("http://example.onion/")

        self.assertEqual("tor", route.transport)
        self.assertEqual("tor", route.profile)

    def test_routes_i2p_hosts_to_i2p(self) -> None:
        route = route_url("http://example.b32.i2p/")

        self.assertEqual("i2p", route.transport)
        self.assertEqual("i2p", route.profile)

    def test_routes_gemini_scheme(self) -> None:
        route = route_url("gemini://wownero.org/")

        self.assertEqual("gemini", route.transport)
        self.assertEqual("gemini", route.profile)

    def test_routes_ipfs_scheme(self) -> None:
        route = route_url("ipfs://bafyexample")

        self.assertEqual("ipfs", route.transport)
        self.assertEqual("ipfs", route.profile)

    def test_routes_ipns_scheme(self) -> None:
        route = route_url("ipns://wownero.example")

        self.assertEqual("ipfs", route.transport)
        self.assertEqual("ipfs", route.profile)

    def test_routes_ipfs_gateway_path(self) -> None:
        route = route_url("/ipfs/bafyexample")

        self.assertEqual("ipfs://bafyexample", route.normalized)
        self.assertEqual("ipfs", route.transport)

    def test_routes_reticulum_family_scheme(self) -> None:
        route = route_url("rns://wownero")

        self.assertEqual("reticulum", route.transport)
        self.assertEqual("reticulum", route.profile)


if __name__ == "__main__":
    unittest.main()
