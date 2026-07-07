from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ampbrowser.docsgen import generate_docs


class DocsGenTest(unittest.TestCase):
    def test_generate_docs_writes_and_then_checks_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            changed = generate_docs(root)

            self.assertEqual(
                {
                    Path("docs/generated/adapters.md"),
                    Path("docs/generated/browser-strategy.md"),
                    Path("docs/generated/candidate-transports.md"),
                    Path("docs/generated/platform-capabilities.md"),
                    Path("docs/generated/route-rules.md"),
                    Path("docs/generated/transports.md"),
                },
                set(changed),
            )
            self.assertEqual([], generate_docs(root, check=True))


if __name__ == "__main__":
    unittest.main()
