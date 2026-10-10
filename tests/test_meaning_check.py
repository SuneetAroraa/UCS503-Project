
import unittest

from code.python.meaning_check import check_meaning


class TestMeaningCheck(unittest.TestCase):

    def test_same_meaning_signals_pass(self):
        result = check_meaning(
            "The drug is not approved for children under 12.",
            "The drug is not approved for children under 12.",
        )
        self.assertTrue(result["safe"])
        self.assertEqual(result["issues"], [])

    def test_lost_negation_is_flagged(self):
        result = check_meaning(
            "The drug is not approved for children.",
            "The drug is approved for children.",
        )
        self.assertFalse(result["safe"])
        self.assertIn("Negation words changed.", result["issues"])

    def test_changed_number_is_flagged(self):
        result = check_meaning(
            "The limit is 20%.",
            "The limit is 25%.",
        )
        self.assertFalse(result["safe"])
        self.assertIn("Numbers or percentages changed.", result["issues"])

    def test_empty_candidate_is_rejected(self):
        result = check_meaning("The system works.", "")
        self.assertFalse(result["safe"])


if __name__ == "__main__":
    unittest.main()
