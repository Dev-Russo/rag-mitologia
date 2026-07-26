import unittest

from langchain_core.documents import Document

from src.ingest import split_documents


class SplitDocumentsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pages = [
            Document(
                page_content=(
                    "Zeus was the ruler of Olympus. Hera was his queen. "
                    "Athena sprang from the head of Zeus."
                ),
                metadata={"page": 0},
            ),
            Document(
                page_content="Persephone was taken to the underworld by Hades.",
                metadata={"page": 1},
            ),
        ]

    def test_preserves_source_page_and_deterministic_id(self) -> None:
        first = split_documents(
            self.pages,
            "bulfinch.pdf",
            chunk_size=60,
            chunk_overlap=10,
        )
        second = split_documents(
            self.pages,
            "bulfinch.pdf",
            chunk_size=60,
            chunk_overlap=10,
        )

        self.assertEqual(
            [chunk.metadata["chunk_id"] for chunk in first],
            [chunk.metadata["chunk_id"] for chunk in second],
        )
        self.assertEqual(first[0].metadata["source"], "bulfinch.pdf")
        self.assertEqual(first[0].metadata["page"], 1)
        self.assertEqual(first[-1].metadata["page"], 2)
        self.assertTrue(all(chunk.page_content.strip() for chunk in first))

    def test_rejects_overlap_greater_than_chunk(self) -> None:
        with self.assertRaises(ValueError):
            split_documents(
                self.pages,
                "bulfinch.pdf",
                chunk_size=50,
                chunk_overlap=50,
            )


if __name__ == "__main__":
    unittest.main()
