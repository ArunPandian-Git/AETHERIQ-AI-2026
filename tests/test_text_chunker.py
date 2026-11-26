import unittest
from backend.document_engine.chunking.text_chunker import TextChunker
class TestTextChunker(unittest.TestCase):
    def test_empty_text_returns_empty_list(self):
        chunker = TextChunker()
        self.assertEqual(chunker.split_text(""), [])
    def test_text_is_split_into_chunks(self):
        chunker = TextChunker(
            chunk_size=12,
            chunk_overlap=4
        )
        chunks = chunker.split_text(
            "one two three four five six"
        )
        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0], "one two")
    def test_chunk_overlap_preserves_context(self):
        chunker = TextChunker(
            chunk_size=12,
            chunk_overlap=4
        )
        chunks = chunker.split_text(
            "one two three four five six"
        )
        self.assertTrue(chunks[1].startswith("two "))
    def test_create_chunks_returns_metadata(self):
        chunker = TextChunker(
            chunk_size=20,
            chunk_overlap=5
        )
        results = chunker.create_chunks(
            text="AETHERIQ AI document testing",
            filename="sample.txt"
        )
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["chunk_id"], 1)
        self.assertEqual(results[0]["filename"], "sample.txt")
        self.assertIn("content", results[0])
        self.assertIn("character_count", results[0])
    def test_invalid_chunk_size_is_rejected(self):
        with self.assertRaises(ValueError):
            TextChunker(chunk_size=0)
    def test_invalid_overlap_is_rejected(self):
        with self.assertRaises(ValueError):
            TextChunker(
                chunk_size=10,
                chunk_overlap=10
            )
if __name__ == "__main__":
    unittest.main()
