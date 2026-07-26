import unittest

import numpy as np
from langchain_core.documents import Document

from src.vector_store import FastEmbedAdapter, index_documents


class FakeVectorStore:
    def __init__(self) -> None:
        self.documents: dict[str, Document] = {}

    def add_documents(
        self,
        documents: list[Document],
        *,
        ids: list[str],
    ) -> None:
        self.documents.update(zip(ids, documents, strict=True))


class IndexDocumentsTests(unittest.TestCase):
    def test_reuses_ids_for_idempotent_upsert(self) -> None:
        store = FakeVectorStore()
        documents = [
            Document(page_content="Zeus", metadata={"chunk_id": "chunk-zeus"}),
            Document(page_content="Hera", metadata={"chunk_id": "chunk-hera"}),
        ]

        self.assertEqual(index_documents(documents, store), 2)
        self.assertEqual(index_documents(documents, store), 2)
        self.assertEqual(set(store.documents), {"chunk-zeus", "chunk-hera"})

    def test_rejects_missing_or_duplicate_ids(self) -> None:
        store = FakeVectorStore()
        with self.assertRaises(ValueError):
            index_documents([Document(page_content="Zeus")], store)
        with self.assertRaises(ValueError):
            index_documents(
                [
                    Document(page_content="Zeus", metadata={"chunk_id": "same"}),
                    Document(page_content="Hera", metadata={"chunk_id": "same"}),
                ],
                store,
            )


class FakeEmbeddingEngine:
    def passage_embed(self, texts: list[str]):
        for index, _ in enumerate(texts):
            yield np.array([float(index), 1.0])

    def query_embed(self, texts: list[str]):
        del texts
        yield np.array([0.5, 1.0])


class FastEmbedAdapterTests(unittest.TestCase):
    def test_adapts_document_and_query_vectors_to_lists(self) -> None:
        adapter = FastEmbedAdapter("unused", engine=FakeEmbeddingEngine())

        self.assertEqual(
            adapter.embed_documents(["Zeus", "Hera"]),
            [[0.0, 1.0], [1.0, 1.0]],
        )
        self.assertEqual(adapter.embed_query("Olimpo"), [0.5, 1.0])


if __name__ == "__main__":
    unittest.main()
