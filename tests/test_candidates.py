from __future__ import annotations

import unittest

from ampbrowser.candidates import CANDIDATE_TRANSPORTS


class CandidateTransportsTest(unittest.TestCase):
    def test_candidate_matrix_contains_next_evaluation_targets(self) -> None:
        by_name = {candidate.name: candidate for candidate in CANDIDATE_TRANSPORTS}

        self.assertIn("ipfs", by_name)
        self.assertIn("yggdrasil", by_name)
        self.assertEqual("next-evaluate", by_name["ipfs"].status)
        self.assertEqual("next-evaluate", by_name["yggdrasil"].status)

    def test_nostr_is_not_classified_as_page_transport(self) -> None:
        by_name = {candidate.name: candidate for candidate in CANDIDATE_TRANSPORTS}

        self.assertEqual("discovery-layer", by_name["nostr"].status)
        self.assertIn("Not a web-page transport", by_name["nostr"].note)


if __name__ == "__main__":
    unittest.main()
