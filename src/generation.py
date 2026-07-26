"""Integração com Claude para reescrita e geração fundamentada."""

from __future__ import annotations

from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from src.config import Settings
from src.retrieval import RetrievedChunk


class QueryRewrite(BaseModel):
    query: str = Field(
        min_length=3,
        description="Consulta curta em inglês para recuperação semântica.",
    )


class Citation(BaseModel):
    chunk_id: str
    quote: str = Field(min_length=3)


class GroundedAnswer(BaseModel):
    answer: str = Field(min_length=3)
    citations: list[Citation] = Field(min_length=1)


def create_chat_model(settings: Settings) -> ChatAnthropic:
    if settings.anthropic_api_key is None:
        raise ValueError("ANTHROPIC_API_KEY não foi configurada")
    return ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key.get_secret_value(),
        temperature=0,
        max_retries=2,
        timeout=30,
    )


def build_query_rewriter(llm: BaseChatModel) -> Runnable[Any, QueryRewrite]:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Rewrite the user's mythology question as a concise English "
                    "semantic-search query for Bulfinch's Mythology. Preserve names "
                    "and intent. Return only the requested structured output."
                ),
            ),
            (
                "human",
                (
                    "Original question: {question}\n"
                    "Previous search query: {current_query}\n"
                    "Retrieval attempt that failed: {attempt}"
                ),
            ),
        ]
    )
    return prompt | llm.with_structured_output(QueryRewrite)


def rewrite_query(
    *,
    question: str,
    current_query: str,
    attempt: int,
    rewriter: Runnable[Any, QueryRewrite],
) -> str:
    result = rewriter.invoke(
        {
            "question": question,
            "current_query": current_query,
            "attempt": attempt,
        }
    )
    rewritten = result.query.strip()
    if rewritten.casefold() == current_query.strip().casefold():
        raise ValueError("Claude devolveu a mesma consulta sem reformulação")
    return rewritten


def build_answer_generator(llm: BaseChatModel) -> Runnable[Any, GroundedAnswer]:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Answer in Brazilian Portuguese using only the supplied excerpts "
                    "from Bulfinch's Mythology. Do not use outside knowledge. Every "
                    "claim must be supported by at least one citation containing the "
                    "exact chunk_id and a verbatim quote from that chunk. If the "
                    "excerpts do not answer the question, say so clearly."
                ),
            ),
            (
                "human",
                "Question: {question}\n\nApproved excerpts:\n{context}",
            ),
        ]
    )
    return prompt | llm.with_structured_output(GroundedAnswer)


def _format_context(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(
        (
            f"<chunk id=\"{chunk.chunk_id}\" source=\"{chunk.source}\" "
            f"page=\"{chunk.page}\">\n{chunk.content}\n</chunk>"
        )
        for chunk in chunks
    )


def generate_answer(
    *,
    question: str,
    chunks: list[RetrievedChunk],
    generator: Runnable[Any, GroundedAnswer],
) -> GroundedAnswer:
    if not chunks:
        raise ValueError("A resposta fundamentada exige ao menos um chunk")

    result = generator.invoke(
        {
            "question": question.strip(),
            "context": _format_context(chunks),
        }
    )
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    for citation in result.citations:
        source = chunks_by_id.get(citation.chunk_id)
        if source is None:
            raise ValueError(f"Citação referencia chunk desconhecido: {citation.chunk_id}")
        if citation.quote not in source.content:
            raise ValueError(
                f"Citação não foi encontrada no chunk {citation.chunk_id}"
            )
    return result
