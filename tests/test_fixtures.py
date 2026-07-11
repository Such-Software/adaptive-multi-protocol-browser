from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ampbrowser.fixtures import check_fixture_manifest


class FixtureCheckTest(unittest.TestCase):
    def test_checks_ampg_manifest_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": "ampg.fixture-manifest.v2",
                        "site": {"id": "wownero", "domain": "wownero.org"},
                        "fixtures": [
                            {
                                "protocol": "clearnet",
                                "url": "https://wownero.org/",
                                "checks": {"transport": "clearnet", "context": "clearnet", "isolation": "transport-context"},
                            },
                            {
                                "protocol": "tor",
                                "url": "http://wownero.onion/",
                                "checks": {
                                    "transport": "tor",
                                    "context": "tor",
                                    "isolation": "transport-context",
                                },
                            },
                            {
                                "protocol": "ipfs",
                                "url": "ipfs://bafyexample",
                                "route": {"match": "/snapshot/*", "fixture_path": "/snapshot/"},
                                "checks": {"transport": "ipfs", "context": "ipfs", "isolation": "transport-context"},
                                "interaction": {"tier": "static"},
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = check_fixture_manifest(path)

        self.assertTrue(result.ok)
        self.assertEqual(3, len(result.checks))
        self.assertEqual("transport-context", result.checks[1].actual_isolation)
        self.assertEqual("/snapshot/*", result.checks[2].route_match)
        self.assertEqual("/snapshot/", result.checks[2].fixture_path)

    def test_reports_route_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": "ampg.fixture-manifest.v1",
                        "site": {"id": "bad", "domain": "example.test"},
                        "fixtures": [
                            {
                                "protocol": "tor",
                                "url": "https://example.test/",
                                "checks": {"transport": "tor", "profile": "tor"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = check_fixture_manifest(path)

        self.assertFalse(result.ok)
        self.assertEqual("fail", result.checks[0].status)
        self.assertIn("transport expected tor got clearnet", result.checks[0].message)

    def test_rejects_transactional_ipfs_fixture(self) -> None:
        result = _check_one(
            "ipfs",
            "ipfs://bafyexample",
            {"tier": "transactional", "payments": "server-invoice"},
        )

        self.assertFalse(result.ok)
        self.assertIn("tier transactional exceeds ipfs max static", result.checks[0].message)
        self.assertIn("payments server-invoice not allowed on ipfs", result.checks[0].message)

    def test_allows_transactional_tor_fixture(self) -> None:
        result = _check_one(
            "tor",
            "http://example.onion/",
            {"tier": "transactional", "identity": "http-session", "payments": "server-invoice"},
        )

        self.assertTrue(result.ok)

    def test_allows_interactive_lite_gemini_but_rejects_realtime(self) -> None:
        ok = _check_one("gemini", "gemini://example.test/", {"tier": "interactive-lite"})
        bad = _check_one("gemini", "gemini://example.test/", {"tier": "realtime", "realtime": True})

        self.assertTrue(ok.ok)
        self.assertFalse(bad.ok)
        self.assertIn("tier realtime exceeds gemini max interactive-lite", bad.checks[0].message)
        self.assertIn("realtime not allowed on gemini", bad.checks[0].message)


def _check_one(transport: str, url: str, interaction: dict) -> object:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "manifest.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "ampg.fixture-manifest.v2",
                    "site": {"id": "example", "domain": "example.test"},
                    "fixtures": [
                        {
                            "protocol": transport,
                            "url": url,
                            "checks": {"transport": transport, "context": transport, "isolation": "transport-context"},
                            "interaction": interaction,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return check_fixture_manifest(path)


if __name__ == "__main__":
    unittest.main()
