
import unittest

from code.python.simplifier import (
    simplify_words,
    simplify_sentences,
    simplify_context,
    simplify_text,
)


class TestSimplifier(unittest.TestCase):

    def test_word_replacement(self):
        text = "The numerous students utilize additional resources."
        expected = "The many students use extra resources."
        self.assertEqual(simplify_words(text), expected)

    def test_capitalization_and_punctuation(self):
        text = "Approximately, numerous students!"
        expected = "About, many students!"
        self.assertEqual(simplify_words(text), expected)

    def test_unknown_words_remain_unchanged(self):
        text = "The students opened their books."
        self.assertEqual(simplify_words(text), text)

    def test_sentence_splitting(self):
        text = (
            "Although the application requires significant resources, "
            "it provides accessibility features that assist users."
        )
        expected = (
            "The application requires significant resources. "
            "It provides accessibility features that assist users."
        )
        self.assertEqual(simplify_sentences(text), expected)

    def test_context_replacement(self):
        text = "The system makes use of numerous computational resources."
        expected = "The system uses a lot of computing power."
        self.assertEqual(simplify_context(text), expected)

    def test_empty_input(self):
        self.assertEqual(simplify_text(""), "")


if __name__ == "__main__":
    unittest.main()
