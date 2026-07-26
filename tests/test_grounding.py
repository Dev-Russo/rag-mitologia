import unittest

from src.grounding import canonical_source_quote


class CanonicalSourceQuoteTests(unittest.TestCase):
    def test_restores_exact_source_punctuation_and_whitespace(self) -> None:
        source = "Jupiter,  or Jove,\n(Zeus,) was the father of gods."
        proposed = "Jupiter or Jove (Zeus) was the father of gods"

        result = canonical_source_quote(proposed, source)

        self.assertEqual(
            result,
            "Jupiter,  or Jove,\n(Zeus,) was the father of gods",
        )

    def test_rejects_paraphrase_with_different_words(self) -> None:
        with self.assertRaises(ValueError):
            canonical_source_quote(
                "Zeus created all of existence",
                "Zeus was the father of gods and men.",
            )


if __name__ == "__main__":
    unittest.main()
