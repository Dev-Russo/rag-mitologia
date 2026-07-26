"""Leitura e fragmentação rastreável do documento-fonte."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from typing import Sequence

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from src.config import get_settings
from src.vector_store import create_vector_store, index_documents

DEFAULT_CHUNK_SIZE = 1_000
DEFAULT_CHUNK_OVERLAP = 150


def normalize_extracted_text(text: str) -> str:
    """Converte a camada OCR posicional em parágrafos legíveis e citáveis."""
    dehyphenated = re.sub(r"-\s*\n\s*(?=[a-z])", "", text)
    paragraphs: list[str] = []
    current_lines: list[str] = []
    for raw_line in dehyphenated.splitlines():
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if line:
            current_lines.append(line)
        elif current_lines:
            paragraphs.append(" ".join(current_lines))
            current_lines = []
    if current_lines:
        paragraphs.append(" ".join(current_lines))
    return "\n\n".join(paragraphs).strip()


def load_pdf(pdf_path: Path) -> list[Document]:
    """Extrai as páginas de um PDF e falha de forma explícita se ele for inválido."""
    path = pdf_path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Documento não encontrado: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"O documento precisa ser um PDF: {path}")

    reader = PdfReader(path)
    pages = [
        Document(
            page_content=normalize_extracted_text(
                page.extract_text(extraction_mode="layout") or ""
            ),
            metadata={"source": path.name, "page": page_index},
        )
        for page_index, page in enumerate(reader.pages)
    ]
    if not pages or not any(page.page_content.strip() for page in pages):
        raise ValueError(f"Nenhum texto foi extraído de {path.name}")
    return pages


def _chunk_id(source: str, page: int, position: int, content: str) -> str:
    identity = f"{source}|{page}|{position}|{content}".encode("utf-8")
    return hashlib.sha256(identity).hexdigest()[:24]


def split_documents(
    pages: Sequence[Document],
    source_name: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Document]:
    """Divide páginas sem perder a referência ao arquivo e à página de origem."""
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap precisa ser menor que chunk_size")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        keep_separator=True,
    )
    chunks: list[Document] = []

    for page_index, page in enumerate(pages):
        page_number = int(page.metadata.get("page", page_index)) + 1
        page_chunks = splitter.split_documents([page])
        for position, chunk in enumerate(page_chunks):
            content = chunk.page_content.strip()
            if not content:
                continue
            metadata = {
                **chunk.metadata,
                "source": source_name,
                "page": page_number,
                "chunk_index": position,
                "chunk_id": _chunk_id(source_name, page_number, position, content),
            }
            chunks.append(Document(page_content=content, metadata=metadata))

    if not chunks:
        raise ValueError("O documento não produziu chunks com texto")
    return chunks


def load_and_split_pdf(
    pdf_path: Path,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Document]:
    pages = load_pdf(pdf_path)
    return split_documents(
        pages,
        pdf_path.name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepara e indexa o corpus mitológico.")
    parser.add_argument("pdf", type=Path, help="Caminho para o documento PDF.")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="Extrai os chunks sem gerar embeddings nem gravar no Chroma.",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Apaga e recria a coleção antes de indexar o documento.",
    )
    args = parser.parse_args()

    chunks = load_and_split_pdf(
        args.pdf,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    pages = {chunk.metadata["page"] for chunk in chunks}
    print(f"Documento preparado: {len(chunks)} chunks em {len(pages)} páginas.")
    if args.prepare_only:
        return

    settings = get_settings()
    vector_store = create_vector_store(
        persist_directory=settings.chroma_path,
        collection_name=settings.chroma_collection,
        model_name=settings.embedding_model,
    )
    if args.rebuild:
        vector_store.reset_collection()
        print(f"Coleção '{settings.chroma_collection}' recriada.")
    indexed = index_documents(chunks, vector_store)
    print(
        f"Indexação concluída: {indexed} chunks na coleção "
        f"'{settings.chroma_collection}'."
    )


if __name__ == "__main__":
    main()
