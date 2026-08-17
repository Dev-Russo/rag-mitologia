import unittest
from typing import Any

from src.generation import (
    Citation,
    GroundedAnswer,
    QueryRewrite,
    generate_answer,
    rewrite_query,
)
from src.retrieval import RetrievedChunk


class FakeRewriter:
    def __init__(self, query: str) -> None:
        self.query = query
        self.received: dict[str, Any] | None = None

    def invoke(self, value: dict[str, Any]) -> QueryRewrite:
        self.received = value
        return QueryRewrite(query=self.query)


class FakeAnswerGenerator:
    def __init__(self, answer: GroundedAnswer) -> None:
        self.answer = answer

    def invoke(self, value: dict[str, Any]) -> GroundedAnswer:
        del value
        return self.answer


class SequenceAnswerGenerator:
    def __init__(self, answers: list[GroundedAnswer]) -> None:
        self.answers = answers
        self.calls: list[dict[str, Any]] = []

    def invoke(self, value: dict[str, Any]) -> GroundedAnswer:
        self.calls.append(value)
        return self.answers[len(self.calls) - 1]


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


class GroundedAnswerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.chunk = RetrievedChunk(
            chunk_id="zeus-1",
            content="Zeus was the ruler of gods and men.",
            source="bulfinch.pdf",
            page=12,
            score=0.9,
        )

    def test_accepts_verbatim_citation_from_known_chunk(self) -> None:
        expected = GroundedAnswer(
            answer="Zeus era o governante dos deuses e dos homens.",
            citations=[
                Citation(
                    chunk_id="zeus-1",
                    quote="Zeus was the ruler of gods and men.",
                )
            ],
        )

        result = generate_answer(
            question="Quem era Zeus?",
            chunks=[self.chunk],
            generator=FakeAnswerGenerator(expected),
        )

        self.assertEqual(result, expected)

    def test_rejects_invented_citation(self) -> None:
        invalid = GroundedAnswer(
            answer="Resposta inválida.",
            citations=[Citation(chunk_id="zeus-1", quote="Invented quotation")],
        )
        with self.assertRaises(ValueError):
            generate_answer(
                question="Quem era Zeus?",
                chunks=[self.chunk],
                generator=FakeAnswerGenerator(invalid),
            )

    def test_retries_when_model_translates_a_citation(self) -> None:
        chunk = RetrievedChunk(
            chunk_id="jupiter-1",
            content=(
                "Jupiter, or Jove, (Zeus,) though called the father of gods "
                "and men, had himself a beginning."
            ),
            source="bulfinch.pdf",
            page=1,
            score=0.9,
        )
        translated = GroundedAnswer(
            answer="O trecho não traz uma lista dos filhos de Zeus.",
            citations=[
                Citation(
                    chunk_id="jupiter-1",
                    quote=(
                        "Jupiter, ou Jove, (Zeus,) though called the father "
                        "of gods and men, had himself a beginning."
                    ),
                )
            ],
        )
        literal = GroundedAnswer(
            answer="O trecho não traz uma lista dos filhos de Zeus.",
            citations=[
                Citation(
                    chunk_id="jupiter-1",
                    quote=(
                        "Jupiter, or Jove, (Zeus,) though called the father "
                        "of gods and men, had himself a beginning."
                    ),
                )
            ],
        )
        generator = SequenceAnswerGenerator([translated, literal])

        result = generate_answer(
            question="Quem são os filhos de Zeus?",
            chunks=[chunk],
            generator=generator,
        )

        self.assertEqual(result, literal)
        self.assertEqual(len(generator.calls), 2)
        self.assertIn("verbatim", generator.calls[1]["grounding_feedback"])


if __name__ == "__main__":
    unittest.main()
