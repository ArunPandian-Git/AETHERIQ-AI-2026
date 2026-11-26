import json
from datetime import datetime, timezone

from google import genai
from google.genai import types

from backend.core.config import settings
from backend.database.connection import get_connection


EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768


class EmbeddingService:

    def __init__(self):

        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "Gemini API key is not configured."
            )

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    def generate_embedding(
        self,
        text: str,
        task_type: str = "RETRIEVAL_DOCUMENT"
    ):

        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        response = self.client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=EMBEDDING_DIMENSIONS
            )
        )

        if not response.embeddings:
            raise RuntimeError(
                "Gemini returned an empty embedding."
            )

        return response.embeddings[0].values

    def embed_document(self, document_id: str):

        connection = get_connection()

        try:

            chunks = connection.execute(
                """
                SELECT id, content
                FROM document_chunks
                WHERE document_id = ?
                ORDER BY chunk_index ASC
                """,
                (document_id,)
            ).fetchall()

            if not chunks:
                raise ValueError(
                    "No document chunks found."
                )

            generated = 0

            for chunk in chunks:

                embedding = self.generate_embedding(
                    chunk["content"],
                    task_type="RETRIEVAL_DOCUMENT"
                )

                connection.execute(
                    """
                    INSERT INTO chunk_embeddings (
                        chunk_id,
                        embedding_model,
                        dimensions,
                        vector_json,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?)

                    ON CONFLICT(chunk_id)
                    DO UPDATE SET
                        embedding_model = excluded.embedding_model,
                        dimensions = excluded.dimensions,
                        vector_json = excluded.vector_json,
                        created_at = excluded.created_at
                    """,
                    (
                        chunk["id"],
                        EMBEDDING_MODEL,
                        len(embedding),
                        json.dumps(embedding),
                        datetime.now(timezone.utc).isoformat()
                    )
                )

                generated += 1

            connection.commit()

            return {
                "success": True,
                "document_id": document_id,
                "embedding_model": EMBEDDING_MODEL,
                "dimensions": EMBEDDING_DIMENSIONS,
                "total_chunks": len(chunks),
                "embeddings_generated": generated
            }

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()


embedding_service = EmbeddingService()