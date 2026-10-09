
import unittest
import spacy

from code.python.readability import (
    count_words,
    count_sentences,
    average_sentence_length,
    find_difficult_words,
    calculate_readability,
)

nlp = spacy.load("en_core_web_sm")


class TestReadability(unittest.TestCase):

    def test_count_words(self):
        doc = nlp("The cat runs.")
        self.assertEqual(count_words(doc), 3)

    def test_count_sentences(self):
        doc = nlp("The cat runs. The dog sleeps.")
        self.assertEqual(count_sentences(doc), 2)

    def test_average_sentence_length(self):
        doc = nlp("The cat runs. The dog sleeps.")
        self.assertEqual(average_sentence_length(doc), 3)

    def test_empty_document(self):
        doc = nlp("")
        self.assertEqual(count_words(doc), 0)
        self.assertEqual(count_sentences(doc), 0)
        self.assertEqual(average_sentence_length(doc), 0)

    def test_difficult_words(self):
        doc = nlp("The implementation requires computational resources.")
        result = find_difficult_words(doc)

        self.assertIn("implementation", result)
        self.assertIn("computational", result)
        self.assertEqual(result, sorted(set(result)))

    def test_calculate_readability_keys(self):
        result = calculate_readability(
            "The cat runs. The dog sleeps."
        )

        expected_keys = {
            "word_count",
            "sentence_count",
            "average_sentence_length",
            "flesch_reading_ease",
            "flesch_kincaid_grade",
            "smog_index",
            "difficult_words",
        }

        self.assertEqual(set(result.keys()), expected_keys)
        self.assertEqual(result["word_count"], 6)
        self.assertEqual(result["sentence_count"], 2)
        self.assertEqual(result["average_sentence_length"], 3)


if __name__ == "__main__":
    unittest.main()
