"""Orquestração do pipeline RAG com ciclo controlado no LangGraph."""

from __future__ import annotations

import hashlib
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

from src.config import Settings
from src.generation import (
    GroundedAnswer,
    generate_answer,
    rewrite_query,
)
from src.graph_extraction import GraphExtraction, extract_graph_concepts
from src.retrieval import RetrievalResult, RetrievedChunk, retrieve


class WorkflowState(TypedDict, total=False):
    question: str
    current_query: str
    attempt: int
    retrieval: RetrievalResult
    answer: GroundedAnswer
    extraction: GraphExtraction


class GraphNode(BaseModel):
    id: str
    label: str
    type: Literal["pergunta", "deus", "heroi", "lugar", "evento"]
    chunk_id: str | None = None
    source_quote: str | None = None


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str


class SourceReference(BaseModel):
    chunk_id: str
    source: str
    page: int
    quote: str
    score: float


class WorkflowEvaluation(BaseModel):
    sufficient: bool
    attempts: int
    final_query: str
    max_score: float


class WorkflowResponse(BaseModel):
    status: Literal["ok", "insufficient", "error"]
    answer: str
    evaluation: WorkflowEvaluation
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    sources: list[SourceReference]
    error: str | None = None


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


class RAGWorkflow:
    def __init__(
        self,
        *,
        vector_store: Any,
        rewriter: Any,
        answer_generator: Any,
        graph_extractor: Any,
        settings: Settings,
    ) -> None:
        self.vector_store = vector_store
        self.rewriter = rewriter
        self.answer_generator = answer_generator
        self.graph_extractor = graph_extractor
        self.settings = settings
        self.graph = self._build_graph()

    def _retrieve(self, state: WorkflowState) -> WorkflowState:
        result = retrieve(
            state["current_query"],
            self.vector_store,
            top_k=self.settings.retrieval_top_k,
            min_score=self.settings.retrieval_min_score,
        )
        return {"retrieval": result}

    def _route_after_retrieval(
        self,
        state: WorkflowState,
    ) -> Literal["answer", "rewrite", "insufficient"]:
        if state["retrieval"].evaluation.sufficient:
            return "answer"
        if state["attempt"] >= self.settings.max_retrieval_attempts:
            return "insufficient"
        return "rewrite"

    def _rewrite(self, state: WorkflowState) -> WorkflowState:
        query = rewrite_query(
            question=state["question"],
            current_query=state["current_query"],
            attempt=state["attempt"],
            rewriter=self.rewriter,
        )
        return {"current_query": query, "attempt": state["attempt"] + 1}

    def _approved_chunks(self, state: WorkflowState) -> list[RetrievedChunk]:
        approved = set(state["retrieval"].evaluation.approved_chunk_ids)
        return [
            chunk for chunk in state["retrieval"].chunks if chunk.chunk_id in approved
        ]

    def _answer(self, state: WorkflowState) -> WorkflowState:
        answer = generate_answer(
            question=state["question"],
            chunks=self._approved_chunks(state),
            generator=self.answer_generator,
        )
        return {"answer": answer}

    def _extract(self, state: WorkflowState) -> WorkflowState:
        extraction = extract_graph_concepts(
            question=state["question"],
            answer=state["answer"].answer,
            chunks=self._approved_chunks(state),
            extractor=self.graph_extractor,
        )
        return {"extraction": extraction}

    @staticmethod
    def _insufficient(state: WorkflowState) -> WorkflowState:
        del state
        return {}

    def _build_graph(self) -> Any:
        builder = StateGraph(WorkflowState)
        builder.add_node("retrieve", self._retrieve)
        builder.add_node("rewrite", self._rewrite)
        builder.add_node("answer", self._answer)
        builder.add_node("extract", self._extract)
        builder.add_node("insufficient", self._insufficient)
        builder.add_edge(START, "retrieve")
        builder.add_conditional_edges(
            "retrieve",
            self._route_after_retrieval,
            {
                "answer": "answer",
                "rewrite": "rewrite",
                "insufficient": "insufficient",
            },
        )
        builder.add_edge("rewrite", "retrieve")
        builder.add_edge("answer", "extract")
        builder.add_edge("extract", END)
        builder.add_edge("insufficient", END)
        return builder.compile()

    def run(self, question: str) -> WorkflowResponse:
        normalized_question = question.strip()
        if not normalized_question:
            raise ValueError("A pergunta não pode estar vazia")

        initial: WorkflowState = {
            "question": normalized_question,
            "current_query": normalized_question,
            "attempt": 1,
        }
        try:
            state = self.graph.invoke(initial)
        except Exception:
            return WorkflowResponse(
                status="error",
                answer="Não foi possível consultar o corpus neste momento.",
                evaluation=WorkflowEvaluation(
                    sufficient=False,
                    attempts=initial["attempt"],
                    final_query=initial["current_query"],
                    max_score=0.0,
                ),
                nodes=[],
                edges=[],
                sources=[],
                error="Falha ao executar o pipeline RAG.",
            )

        retrieval = state["retrieval"]
        evaluation = WorkflowEvaluation(
            sufficient=retrieval.evaluation.sufficient,
            attempts=state["attempt"],
            final_query=state["current_query"],
            max_score=retrieval.evaluation.max_score,
        )
        if not retrieval.evaluation.sufficient:
            return WorkflowResponse(
                status="insufficient",
                answer=(
                    "Não encontrei evidências suficientes no documento para responder "
                    "a essa pergunta."
                ),
                evaluation=evaluation,
                nodes=[],
                edges=[],
                sources=[],
            )

        return self._success_response(state, evaluation)

    def _success_response(
        self,
        state: WorkflowState,
        evaluation: WorkflowEvaluation,
    ) -> WorkflowResponse:
        root_id = _stable_id("question", state["question"])
        nodes = [
            GraphNode(id=root_id, label=state["question"], type="pergunta")
        ]
        edges: list[GraphEdge] = []
        for concept in state["extraction"].concepts:
            node_id = _stable_id(
                "concept",
                f"{concept.name}|{concept.chunk_id}",
            )
            nodes.append(
                GraphNode(
                    id=node_id,
                    label=concept.name,
                    type=concept.type,
                    chunk_id=concept.chunk_id,
                    source_quote=concept.source_quote,
                )
            )
            edges.append(
                GraphEdge(
                    source=root_id,
                    target=node_id,
                    relation=concept.relation,
                )
            )

        chunks_by_id = {
            chunk.chunk_id: chunk for chunk in self._approved_chunks(state)
        }
        sources = [
            SourceReference(
                chunk_id=citation.chunk_id,
                source=chunks_by_id[citation.chunk_id].source,
                page=chunks_by_id[citation.chunk_id].page,
                quote=citation.quote,
                score=chunks_by_id[citation.chunk_id].score,
            )
            for citation in state["answer"].citations
        ]
        return WorkflowResponse(
            status="ok",
            answer=state["answer"].answer,
            evaluation=evaluation,
            nodes=nodes,
            edges=edges,
            sources=sources,
        )
