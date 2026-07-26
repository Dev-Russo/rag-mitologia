import unittest

from langchain_core.documents import Document

from src.retrieval import RetrievedChunk, evaluate_chunks, retrieve


class FakeRetrieverStore:
    def similarity_search_with_relevance_scores(
        self,
        query: str,
        *,
        k: int,
    ) -> list[tuple[Document, float]]:
        del query
        matches = [
            (
                Document(
                    page_content="Zeus ruled Olympus.",
                    metadata={
                        "chunk_id": "zeus",
                        "source": "bulfinch.pdf",
                        "page": 12,
                    },
                ),
                0.82,
            ),
            (
                Document(
                    page_content="A distant unrelated passage.",
                    metadata={
                        "chunk_id": "other",
                        "source": "bulfinch.pdf",
                        "page": 99,
                    },
                ),
                0.21,
            ),
        ]
        return matches[:k]


class RetrievalTests(unittest.TestCase):
    def test_retrieves_and_approves_chunks_above_threshold(self) -> None:
        result = retrieve(
            "Quem governa o Olimpo?",
            FakeRetrieverStore(),
            top_k=2,
            min_score=0.45,
        )

        self.assertTrue(result.evaluation.sufficient)
        self.assertEqual(result.evaluation.approved_chunk_ids, ["zeus"])
        self.assertEqual(result.chunks[0].page, 12)

    def test_marks_low_scores_as_insufficient(self) -> None:
        chunks = [
            RetrievedChunk(
                chunk_id="low",
                content="Irrelevant",
                source="bulfinch.pdf",
                page=1,
                score=0.2,
            )
        ]

        evaluation = evaluate_chunks(chunks, min_score=0.45)

        self.assertFalse(evaluation.sufficient)
        self.assertEqual(evaluation.approved_chunk_ids, [])
        self.assertEqual(evaluation.max_score, 0.2)

    def test_rejects_empty_query(self) -> None:
        with self.assertRaises(ValueError):
            retrieve("   ", FakeRetrieverStore())


if __name__ == "__main__":
    unittest.main()
