"""Recuperação semântica e avaliação determinística do contexto."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    chunk_id: str
    content: str
    source: str
    page: int
    score: float = Field(ge=0.0, le=1.0)


class RetrievalEvaluation(BaseModel):
    sufficient: bool
    threshold: float
    max_score: float
    approved_chunk_ids: list[str]


class RetrievalResult(BaseModel):
    query: str
    chunks: list[RetrievedChunk]
    evaluation: RetrievalEvaluation


def evaluate_chunks(
    chunks: list[RetrievedChunk],
    *,
    min_score: float,
) -> RetrievalEvaluation:
    if not 0.0 <= min_score <= 1.0:
        raise ValueError("min_score precisa estar entre 0 e 1")

    approved = [chunk.chunk_id for chunk in chunks if chunk.score >= min_score]
    max_score = max((chunk.score for chunk in chunks), default=0.0)
    return RetrievalEvaluation(
        sufficient=bool(approved),
        threshold=min_score,
        max_score=max_score,
        approved_chunk_ids=approved,
    )


def retrieve(
    query: str,
    vector_store: Any,
    *,
    top_k: int = 5,
    min_score: float = 0.40,
) -> RetrievalResult:
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("A consulta não pode estar vazia")
    if top_k < 1:
        raise ValueError("top_k precisa ser maior que zero")

    matches = vector_store.similarity_search_with_relevance_scores(
        normalized_query,
        k=top_k,
    )
    chunks: list[RetrievedChunk] = []
    for document, raw_score in matches:
        metadata = document.metadata
        chunks.append(
            RetrievedChunk(
                chunk_id=str(metadata["chunk_id"]),
                content=document.page_content,
                source=str(metadata["source"]),
                page=int(metadata["page"]),
                score=max(0.0, min(1.0, float(raw_score))),
            )
        )
    chunks.sort(key=lambda chunk: chunk.score, reverse=True)

    return RetrievalResult(
        query=normalized_query,
        chunks=chunks,
        evaluation=evaluate_chunks(chunks, min_score=min_score),
    )
