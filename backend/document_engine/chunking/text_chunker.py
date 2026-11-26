from typing import List, Dict


class TextChunker:

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):

        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive.")

        if chunk_overlap < 0:
            raise ValueError("Chunk overlap cannot be negative.")

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "Chunk overlap must be smaller than chunk size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:

        if not text or not text.strip():
            return []

        words = text.split()

        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:

            additional_length = len(word) + (
                1 if current_chunk else 0
            )

            if (
                current_length + additional_length
                > self.chunk_size
                and current_chunk
            ):

                chunks.append(" ".join(current_chunk))

                overlap_words = []
                overlap_length = 0

                for previous_word in reversed(current_chunk):

                    word_length = len(previous_word) + (
                        1 if overlap_words else 0
                    )

                    if (
                        overlap_length + word_length
                        > self.chunk_overlap
                    ):
                        break

                    overlap_words.insert(0, previous_word)
                    overlap_length += word_length

                current_chunk = overlap_words
                current_length = len(" ".join(current_chunk))

            if current_chunk:
                current_length += 1

            current_chunk.append(word)
            current_length += len(word)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def create_chunks(
        self,
        text: str,
        filename: str
    ) -> List[Dict]:

        text_chunks = self.split_text(text)

        results = []

        for index, chunk in enumerate(
            text_chunks,
            start=1
        ):

            results.append({
                "chunk_id": index,
                "filename": filename,
                "content": chunk,
                "character_count": len(chunk)
            })

        return results


text_chunker = TextChunker()