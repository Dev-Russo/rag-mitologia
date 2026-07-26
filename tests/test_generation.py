import unittest
from typing import Any

from src.generation import QueryRewrite, rewrite_query


class FakeRewriter:
    def __init__(self, query: str) -> None:
        self.query = query
        self.received: dict[str, Any] | None = None

    def invoke(self, value: dict[str, Any]) -> QueryRewrite:
        self.received = value
        return QueryRewrite(query=self.query)


class QueryRewriteTests(unittest.TestCase):
    def test_returns_structured_rewritten_query(self) -> None:
        rewriter = FakeRewriter("children of Zeus in Greek mythology")

        result = rewrite_query(
            question="Quem são os filhos de Zeus?",
            current_query="Quem são os filhos de Zeus?",
            attempt=1,
            rewriter=rewriter,
        )

        self.assertEqual(result, "children of Zeus in Greek mythology")
        self.assertEqual(rewriter.received["attempt"], 1)

    def test_rejects_unchanged_query(self) -> None:
        rewriter = FakeRewriter("Zeus")
        with self.assertRaises(ValueError):
            rewrite_query(
                question="Zeus",
                current_query="Zeus",
                attempt=1,
                rewriter=rewriter,
            )


if __name__ == "__main__":
    unittest.main()
