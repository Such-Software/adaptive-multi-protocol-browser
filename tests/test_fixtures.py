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
                        "schema": "ampg.fixture-manifest.v1",
                        "site": {"id": "wownero", "domain": "wownero.org"},
                        "fixtures": [
                            {
                                "protocol": "clearnet",
                                "url": "https://wownero.org/",
                                "checks": {"transport": "clearnet", "profile": "clearnet"},
                            },
                            {
                                "protocol": "tor",
                                "url": "http://wownero.onion/",
                                "checks": {"transport": "tor", "profile": "tor"},
                            },
                            {
                                "protocol": "ipfs",
                                "url": "ipfs://bafyexample",
                                "checks": {"transport": "ipfs", "profile": "ipfs"},
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = check_fixture_manifest(path)

        self.assertTrue(result.ok)
        self.assertEqual(3, len(result.checks))

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


if __name__ == "__main__":
    unittest.main()
