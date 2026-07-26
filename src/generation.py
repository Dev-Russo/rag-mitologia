"""Integração com Claude para reescrita e geração fundamentada."""

from __future__ import annotations

from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from src.config import Settings


class QueryRewrite(BaseModel):
    query: str = Field(
        min_length=3,
        description="Consulta curta em inglês para recuperação semântica.",
    )


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
