import unittest
from unittest.mock import patch

from code.python.hybrid_engine import process_text_with_mode


class TestHybridEngine(unittest.TestCase):

    def test_rules_mode_does_not_call_gemini(self):
        with patch(
            "code.python.hybrid_engine.simplify_with_gemini"
        ) as mock_gemini:
            result = process_text_with_mode(
                "The application requires resources.",
                "rules",
            )

        mock_gemini.assert_not_called()
        self.assertEqual(result["selected_engine"], "rules")
        self.assertIsNone(result["llm_text"])

    def test_hybrid_uses_gemini_when_check_passes(self):
        text = (
            "Although the application requires significant resources, "
            "it provides accessibility features that assist users."
        )
        candidate = (
            "The application needs a lot of resources, "
            "but it provides accessibility features that help users."
        )

        with patch(
            "code.python.hybrid_engine.simplify_with_gemini",
            return_value=candidate,
        ):
            result = process_text_with_mode(text, "hybrid")

        self.assertEqual(result["selected_engine"], "llm")
        self.assertFalse(result["fallback_used"])
        self.assertTrue(result["meaning_check"]["safe"])

    def test_hybrid_falls_back_if_negation_changes(self):
        text = "The drug is not approved for children under 12."
        candidate = "The drug is approved for children under 12."

        with patch(
            "code.python.hybrid_engine.simplify_with_gemini",
            return_value=candidate,
        ):
            result = process_text_with_mode(text, "hybrid")

        self.assertEqual(result["selected_engine"], "rules")
        self.assertTrue(result["fallback_used"])
        self.assertFalse(result["meaning_check"]["safe"])

    def test_hybrid_falls_back_if_gemini_fails(self):
        with patch(
            "code.python.hybrid_engine.simplify_with_gemini",
            side_effect=RuntimeError("Simulated API failure"),
        ):
            result = process_text_with_mode(
                "The application requires resources.",
                "hybrid",
            )

        self.assertEqual(result["selected_engine"], "rules")
        self.assertTrue(result["fallback_used"])


if __name__ == "__main__":
    unittest.main()