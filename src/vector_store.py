"""Configuração dos embeddings locais e da coleção persistente do Chroma."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings


def create_embeddings(model_name: str) -> Embeddings:
    return FastEmbedEmbeddings(model_name=model_name)


def create_vector_store(
    *,
    persist_directory: Path,
    collection_name: str,
    model_name: str,
    embedding: Embeddings | None = None,
) -> Chroma:
    persist_directory.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=collection_name,
        embedding_function=embedding or create_embeddings(model_name),
        persist_directory=str(persist_directory),
        collection_metadata={"hnsw:space": "cosine"},
    )


def index_documents(documents: Sequence[Document], vector_store: Any) -> int:
    """Faz upsert usando os chunk_ids estáveis como IDs do Chroma."""
    if not documents:
        raise ValueError("Nenhum documento foi recebido para indexação")

    ids: list[str] = []
    for document in documents:
        chunk_id = document.metadata.get("chunk_id")
        if not isinstance(chunk_id, str) or not chunk_id:
            raise ValueError("Todo documento precisa de um chunk_id")
        ids.append(chunk_id)

    if len(ids) != len(set(ids)):
        raise ValueError("Foram encontrados chunk_ids duplicados")

    vector_store.add_documents(list(documents), ids=ids)
    return len(documents)
