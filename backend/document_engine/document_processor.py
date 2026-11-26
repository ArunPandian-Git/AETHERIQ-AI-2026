from pathlib import Path

from backend.document_engine.loaders.document_loader import (
    document_loader,
    DocumentProcessingError
)

from backend.document_engine.chunking.text_chunker import (
    TextChunker
)


class DocumentProcessor:

    def __init__(
        self,
        chunk_size=1000,
        chunk_overlap=200
    ):

        self.chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def process_document(
        self,
        file_bytes: bytes,
        filename: str
    ):

        if not filename:
            raise DocumentProcessingError(
                "Filename is required."
            )

        # STEP 1: Extract document text

        extracted = document_loader.extract_text(
            file_bytes,
            filename
        )

        document_text = extracted["text"]

        # STEP 2: Generate text chunks

        chunks = self.chunker.create_chunks(
            text=document_text,
            filename=filename
        )

        # STEP 3: Prepare metadata

        metadata = {
            "filename": filename,
            "file_type": Path(filename).suffix.lower(),
            "character_count": len(document_text),
            "total_chunks": len(chunks),
            "chunk_size": self.chunker.chunk_size,
            "chunk_overlap": self.chunker.chunk_overlap
        }

        # STEP 4: Return processing results

        return {
            "success": True,
            "message": "Document processed successfully.",
            "metadata": metadata,
            "chunks": chunks,
            "extracted_text": document_text
        }


document_processor = DocumentProcessor()