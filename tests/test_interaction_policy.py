from __future__ import annotations

import unittest

from ampbrowser.interaction_policy import interaction_failures


class InteractionPolicyTest(unittest.TestCase):
    def test_static_ipfs_is_allowed(self) -> None:
        self.assertEqual(
            [],
            interaction_failures(
                "ipfs",
                tier="static",
                identity="none",
                payments="none",
                realtime=False,
                public_allowed=True,
            ),
        )

    def test_public_allowed_false_fails(self) -> None:
        failures = interaction_failures(
            "tor",
            tier="static",
            identity="none",
            payments="none",
            realtime=False,
            public_allowed=False,
        )

        self.assertEqual(["fixture is not public_allowed"], failures)


if __name__ == "__main__":
    unittest.main()
