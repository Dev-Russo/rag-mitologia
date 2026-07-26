import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app import app, get_workflow
from src.workflow import (
    GraphEdge,
    GraphNode,
    SourceReference,
    WorkflowEvaluation,
    WorkflowResponse,
)


class FakeWorkflow:
    def __init__(self, response: WorkflowResponse) -> None:
        self.response = response
        self.questions: list[str] = []

    def run(self, question: str) -> WorkflowResponse:
        self.questions.append(question)
        return self.response.model_copy(deep=True)


def success_response() -> WorkflowResponse:
    return WorkflowResponse(
        status="ok",
        answer="Zeus governa o Olimpo.",
        evaluation=WorkflowEvaluation(
            sufficient=True,
            attempts=1,
            final_query="Zeus Olympus",
            max_score=0.8,
        ),
        nodes=[
            GraphNode(id="question:1", label="Pergunta", type="pergunta"),
            GraphNode(
                id="concept:zeus",
                label="Zeus",
                type="deus",
                chunk_id="chunk-1",
                source_quote="Zeus ruled Olympus.",
            ),
        ],
        edges=[
            GraphEdge(
                source="question:1",
                target="concept:zeus",
                relation="governa",
            )
        ],
        sources=[
            SourceReference(
                chunk_id="chunk-1",
                source="bulfinch.pdf",
                page=10,
                quote="Zeus ruled Olympus.",
                score=0.8,
            )
        ],
    )


class AppRoutesTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_query_returns_workflow_contract(self) -> None:
        workflow = FakeWorkflow(success_response())
        app.dependency_overrides[get_workflow] = lambda: workflow

        with TestClient(app) as client:
            response = client.post("/query", json={"question": "Quem era Zeus?"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(workflow.questions, ["Quem era Zeus?"])

    def test_expand_attaches_children_to_clicked_node(self) -> None:
        workflow = FakeWorkflow(success_response())
        app.dependency_overrides[get_workflow] = lambda: workflow

        with TestClient(app) as client:
            response = client.post(
                "/expand",
                json={"node_id": "existing:hera", "concept": "Hera"},
            )

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("pergunta", {node["type"] for node in body["nodes"]})
        self.assertEqual(body["edges"][0]["source"], "existing:hera")
        self.assertIn("Hera", workflow.questions[0])

    def test_rejects_invalid_question(self) -> None:
        app.dependency_overrides[get_workflow] = lambda: FakeWorkflow(
            success_response()
        )
        with TestClient(app) as client:
            response = client.post("/query", json={"question": " "})
        self.assertEqual(response.status_code, 422)

    def test_returns_service_unavailable_for_controlled_error(self) -> None:
        failed = success_response().model_copy(
            update={
                "status": "error",
                "answer": "Não foi possível consultar o corpus.",
                "nodes": [],
                "edges": [],
                "sources": [],
                "error": "Falha ao executar o pipeline RAG.",
            }
        )
        app.dependency_overrides[get_workflow] = lambda: FakeWorkflow(failed)

        with TestClient(app) as client:
            response = client.post("/query", json={"question": "Quem era Zeus?"})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "error")

    def test_reconnects_after_chroma_collection_rebuild(self) -> None:
        stale_store = MagicMock()
        stale_store.get.side_effect = RuntimeError("collection no longer exists")
        stale = SimpleNamespace(vector_store=stale_store)
        fresh_store = MagicMock()
        fresh = SimpleNamespace(vector_store=fresh_store)

        with patch(
            "app._cached_workflow",
            side_effect=[stale, fresh],
        ) as cached:
            result = get_workflow()

        self.assertIs(result, fresh)
        cached.cache_clear.assert_called_once()
        fresh_store.get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
