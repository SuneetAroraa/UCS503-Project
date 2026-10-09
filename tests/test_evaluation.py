
import unittest

from code.python.evaluation import (
    compare_readability,
    summarize_improvement,
)


class TestEvaluation(unittest.TestCase):

    def setUp(self):
        self.original = {
            "word_count": 100,
            "sentence_count": 5,
            "average_sentence_length": 20.0,
            "flesch_reading_ease": 45.0,
            "flesch_kincaid_grade": 12.0,
            "smog_index": 10.0,
            "difficult_words": ["implementation", "computational", "significant"],
        }

        self.simplified = {
            "word_count": 85,
            "sentence_count": 7,
            "average_sentence_length": 12.14,
            "flesch_reading_ease": 65.0,
            "flesch_kincaid_grade": 8.0,
            "smog_index": 7.0,
            "difficult_words": ["implementation"],
        }

    def test_compare_readability_changes(self):
        result = compare_readability(self.original, self.simplified)

        self.assertEqual(result["word_count"]["change"], -15)
        self.assertEqual(result["sentence_count"]["change"], 2)
        self.assertEqual(result["flesch_reading_ease"]["change"], 20.0)
        self.assertEqual(result["flesch_kincaid_grade"]["change"], -4.0)
        self.assertEqual(result["smog_index"]["change"], -3.0)
        self.assertEqual(result["difficult_word_count"]["change"], -2)

    def test_comparison_contains_all_metrics(self):
        result = compare_readability(self.original, self.simplified)

        expected_keys = {
            "word_count",
            "sentence_count",
            "average_sentence_length",
            "flesch_reading_ease",
            "flesch_kincaid_grade",
            "smog_index",
            "difficult_word_count",
        }

        self.assertEqual(set(result.keys()), expected_keys)

    def test_improvement_detected(self):
        comparison = compare_readability(self.original, self.simplified)
        result = summarize_improvement(comparison)

        self.assertTrue(result["readability_improved"])
        self.assertEqual(result["flesch_improvement"], 20.0)
        self.assertEqual(result["grade_level_reduction"], 4.0)
        self.assertEqual(result["smog_reduction"], 3.0)
        self.assertEqual(result["difficult_words_reduced"], 2)

    def test_improvement_not_detected(self):
        comparison = compare_readability(self.original, self.original)
        result = summarize_improvement(comparison)

        self.assertFalse(result["readability_improved"])


if __name__ == "__main__":
    unittest.main()
