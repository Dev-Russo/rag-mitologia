"""Extração estruturada e validada dos conceitos exibidos no grafo."""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from src.retrieval import RetrievedChunk

NodeType = Literal["deus", "heroi", "lugar", "evento"]


class GraphConcept(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    type: NodeType
    relation: str = Field(min_length=2, max_length=160)
    chunk_id: str
    source_quote: str = Field(min_length=3)


class GraphExtraction(BaseModel):
    concepts: list[GraphConcept] = Field(min_length=3, max_length=6)


def build_graph_extractor(llm: BaseChatModel) -> Runnable[Any, GraphExtraction]:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Extract 3 to 6 concepts for an interactive mythology graph. "
                    "Allowed types are deus, heroi, lugar and evento. Each concept "
                    "must be supported by one supplied chunk_id and an exact verbatim "
                    "quote from that chunk. Describe its relation to the parent "
                    "question in Brazilian Portuguese. Do not invent entities."
                ),
            ),
            (
                "human",
                (
                    "Parent question: {question}\n"
                    "Grounded answer: {answer}\n\n"
                    "Approved excerpts:\n{context}"
                ),
            ),
        ]
    )
    return prompt | llm.with_structured_output(GraphExtraction)


def _format_context(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(
        f"[{chunk.chunk_id}] {chunk.content}" for chunk in chunks
    )


def extract_graph_concepts(
    *,
    question: str,
    answer: str,
    chunks: list[RetrievedChunk],
    extractor: Runnable[Any, GraphExtraction],
) -> GraphExtraction:
    if not chunks:
        raise ValueError("A extração do grafo exige chunks aprovados")

    result = extractor.invoke(
        {
            "question": question,
            "answer": answer,
            "context": _format_context(chunks),
        }
    )
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    seen_names: set[str] = set()
    for concept in result.concepts:
        normalized_name = concept.name.strip().casefold()
        if normalized_name in seen_names:
            raise ValueError(f"Conceito duplicado: {concept.name}")
        seen_names.add(normalized_name)

        source = chunks_by_id.get(concept.chunk_id)
        if source is None:
            raise ValueError(
                f"Conceito referencia chunk desconhecido: {concept.chunk_id}"
            )
        if concept.source_quote not in source.content:
            raise ValueError(
                f"Trecho do conceito não existe no chunk {concept.chunk_id}"
            )
    return result
