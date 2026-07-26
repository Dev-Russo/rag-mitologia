"""Extração estruturada e validada dos conceitos exibidos no grafo."""

from __future__ import annotations

import logging
from typing import Any, Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from src.grounding import canonical_source_quote, closest_source_quote
from src.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

NodeType = Literal["deus", "heroi", "lugar", "evento"]


class GraphConcept(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    type: NodeType
    relation: str = Field(min_length=2, max_length=160)
    chunk_id: str
    source_quote: str = Field(min_length=3)


class GraphExtraction(BaseModel):
    concepts: list[GraphConcept] = Field(max_length=6)


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
    validated_concepts: list[GraphConcept] = []
    seen_names: set[str] = set()
    for concept in result.concepts:
        normalized_name = concept.name.strip().casefold()
        if normalized_name in seen_names:
            logger.warning("Conceito duplicado descartado: %s", concept.name)
            continue

        source = chunks_by_id.get(concept.chunk_id)
        if source is None:
            logger.warning(
                "Conceito %s descartado por referenciar chunk desconhecido",
                concept.name,
            )
            continue
        try:
            concept.source_quote = canonical_source_quote(
                concept.source_quote,
                source.content,
            )
        except ValueError:
            try:
                concept.source_quote = closest_source_quote(
                    concept.source_quote,
                    source.content,
                    concept_name=concept.name,
                    relation=concept.relation,
                )
            except ValueError:
                logger.warning(
                    "Conceito %s descartado por não possuir evidência no chunk",
                    concept.name,
                )
                continue
            logger.info(
                "Citação do conceito %s recuperada diretamente do chunk",
                concept.name,
            )

        seen_names.add(normalized_name)
        validated_concepts.append(concept)
    return GraphExtraction(concepts=validated_concepts)
