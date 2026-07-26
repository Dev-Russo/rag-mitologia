import unittest
from typing import Any

from src.graph_extraction import (
    GraphConcept,
    GraphExtraction,
    extract_graph_concepts,
)
from src.retrieval import RetrievedChunk


class FakeExtractor:
    def __init__(self, extraction: GraphExtraction) -> None:
        self.extraction = extraction

    def invoke(self, value: dict[str, Any]) -> GraphExtraction:
        del value
        return self.extraction


def make_extraction(quote: str) -> GraphExtraction:
    return GraphExtraction(
        concepts=[
            GraphConcept(
                name="Zeus",
                type="deus",
                relation="governa o Olimpo",
                chunk_id="myth-1",
                source_quote=quote,
            ),
            GraphConcept(
                name="Hera",
                type="deus",
                relation="é rainha ao lado de Zeus",
                chunk_id="myth-1",
                source_quote="Hera was his queen.",
            ),
            GraphConcept(
                name="Olimpo",
                type="lugar",
                relation="é governado por Zeus",
                chunk_id="myth-1",
                source_quote="Zeus ruled Olympus.",
            ),
        ]
    )


class GraphExtractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.chunk = RetrievedChunk(
            chunk_id="myth-1",
            content="Zeus ruled Olympus. Hera was his queen.",
            source="bulfinch.pdf",
            page=10,
            score=0.9,
        )

    def test_accepts_concepts_with_real_source_quotes(self) -> None:
        extraction = make_extraction("Zeus ruled Olympus.")

        result = extract_graph_concepts(
            question="Quem governa o Olimpo?",
            answer="Zeus governa o Olimpo.",
            chunks=[self.chunk],
            extractor=FakeExtractor(extraction),
        )

        self.assertEqual(len(result.concepts), 3)

    def test_rejects_concept_with_invented_quote(self) -> None:
        extraction = make_extraction("Zeus created the world.")
        with self.assertRaises(ValueError):
            extract_graph_concepts(
                question="Quem governa o Olimpo?",
                answer="Zeus governa o Olimpo.",
                chunks=[self.chunk],
                extractor=FakeExtractor(extraction),
            )


if __name__ == "__main__":
    unittest.main()
