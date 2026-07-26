import unittest
from typing import Any
from unittest.mock import patch

from langchain_core.documents import Document

from src.config import Settings
from src.generation import Citation, GroundedAnswer, QueryRewrite
from src.graph_extraction import GraphConcept, GraphExtraction
from src.workflow import RAGWorkflow, create_rag_workflow


class SequenceStore:
    def __init__(self, scores: list[float]) -> None:
        self.scores = scores
        self.queries: list[str] = []

    def similarity_search_with_relevance_scores(
        self,
        query: str,
        *,
        k: int,
    ) -> list[tuple[Document, float]]:
        del k
        self.queries.append(query)
        score = self.scores[min(len(self.queries) - 1, len(self.scores) - 1)]
        document = Document(
            page_content="Zeus ruled Olympus. Hera was his queen.",
            metadata={
                "chunk_id": "myth-1",
                "source": "bulfinch.pdf",
                "page": 10,
            },
        )
        return [(document, score)]


class SequenceRewriter:
    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, value: dict[str, Any]) -> QueryRewrite:
        del value
        self.calls += 1
        return QueryRewrite(query=f"rewritten mythology query {self.calls}")


class StaticAnswerGenerator:
    def invoke(self, value: dict[str, Any]) -> GroundedAnswer:
        del value
        return GroundedAnswer(
            answer="Zeus governava o Olimpo.",
            citations=[
                Citation(chunk_id="myth-1", quote="Zeus ruled Olympus.")
            ],
        )


class StaticGraphExtractor:
    def invoke(self, value: dict[str, Any]) -> GraphExtraction:
        del value
        return GraphExtraction(
            concepts=[
                GraphConcept(
                    name="Zeus",
                    type="deus",
                    relation="governa",
                    chunk_id="myth-1",
                    source_quote="Zeus ruled Olympus.",
                ),
                GraphConcept(
                    name="Hera",
                    type="deus",
                    relation="é rainha",
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


def make_workflow(store: SequenceStore, rewriter: SequenceRewriter) -> RAGWorkflow:
    settings = Settings(
        _env_file=None,
        retrieval_top_k=5,
        retrieval_min_score=0.45,
        max_retrieval_attempts=3,
    )
    return RAGWorkflow(
        vector_store=store,
        rewriter=rewriter,
        answer_generator=StaticAnswerGenerator(),
        graph_extractor=StaticGraphExtractor(),
        settings=settings,
    )


class WorkflowTests(unittest.TestCase):
    def test_rewrites_until_third_retrieval_then_succeeds(self) -> None:
        store = SequenceStore([0.2, 0.3, 0.9])
        rewriter = SequenceRewriter()

        result = make_workflow(store, rewriter).run("Quem governa o Olimpo?")

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.evaluation.attempts, 3)
        self.assertEqual(rewriter.calls, 2)
        self.assertEqual(len(store.queries), 3)
        self.assertEqual(len(result.nodes), 4)
        self.assertEqual(len(result.edges), 3)
        self.assertEqual(result.sources[0].page, 10)

    def test_stops_after_three_insufficient_retrievals(self) -> None:
        store = SequenceStore([0.1, 0.2, 0.3])
        rewriter = SequenceRewriter()

        result = make_workflow(store, rewriter).run("Pergunta fora do corpus")

        self.assertEqual(result.status, "insufficient")
        self.assertEqual(result.evaluation.attempts, 3)
        self.assertEqual(rewriter.calls, 2)
        self.assertEqual(len(store.queries), 3)
        self.assertEqual(result.nodes, [])

    def test_returns_controlled_error_when_dependency_fails(self) -> None:
        class FailingStore:
            def similarity_search_with_relevance_scores(
                self,
                query: str,
                *,
                k: int,
            ) -> list[Any]:
                del query, k
                raise TimeoutError

        workflow = make_workflow(FailingStore(), SequenceRewriter())
        result = workflow.run("Quem era Zeus?")

        self.assertEqual(result.status, "error")
        self.assertIsNotNone(result.error)

    def test_factory_connects_real_components(self) -> None:
        settings = Settings(_env_file=None)
        store = SequenceStore([0.9])
        rewriter = SequenceRewriter()
        answer_generator = StaticAnswerGenerator()
        graph_extractor = StaticGraphExtractor()

        with (
            patch("src.workflow.create_vector_store", return_value=store),
            patch("src.workflow.create_chat_model", return_value=object()),
            patch("src.workflow.build_query_rewriter", return_value=rewriter),
            patch(
                "src.workflow.build_answer_generator",
                return_value=answer_generator,
            ),
            patch(
                "src.workflow.build_graph_extractor",
                return_value=graph_extractor,
            ),
        ):
            workflow = create_rag_workflow(settings)

        self.assertIsInstance(workflow, RAGWorkflow)
        self.assertIs(workflow.vector_store, store)


if __name__ == "__main__":
    unittest.main()
