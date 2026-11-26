import json
import numpy as np

from backend.database.connection import get_connection

from backend.ai_engine.providers.embedding_service import (
    embedding_service,
    EMBEDDING_MODEL
)


class SemanticSearch:

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: str = None,
        min_similarity: float = 0.0
    ):

        # Validate search query
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        # Validate retrieval quantity
        if not isinstance(top_k, int) or not 1 <= top_k <= 20:
            raise ValueError("top_k must be between 1 and 20.")

        # Validate similarity threshold
        if not -1.0 <= min_similarity <= 1.0:
            raise ValueError(
                "min_similarity must be between -1.0 and 1.0."
            )

        # Generate query embedding
        query_vector = np.asarray(
            embedding_service.generate_embedding(
                query.strip(),
                task_type="RETRIEVAL_QUERY"
            ),
            dtype=np.float32
        )

        if query_vector.ndim != 1 or query_vector.size == 0:
            raise ValueError("Invalid query embedding.")

        if not np.all(np.isfinite(query_vector)):
            raise ValueError("Query embedding contains invalid values.")

        query_norm = np.linalg.norm(query_vector)

        if query_norm == 0:
            raise ValueError("Invalid query embedding.")

        connection = get_connection()

        try:

            sql = """
                SELECT
                    dc.id AS chunk_id,
                    dc.document_id,
                    dc.chunk_index,
                    dc.content,
                    d.filename,
                    ce.vector_json
                FROM document_chunks dc

                INNER JOIN chunk_embeddings ce
                    ON dc.id = ce.chunk_id

                INNER JOIN documents d
                    ON dc.document_id = d.id

                WHERE ce.embedding_model = ?
            """

            parameters = [EMBEDDING_MODEL]

            # Optional document-specific search
            if document_id:
                sql += " AND dc.document_id = ?"
                parameters.append(document_id)

            rows = connection.execute(
                sql,
                parameters
            ).fetchall()

            results = []
            invalid_embeddings = 0

            # Calculate cosine similarity
            for row in rows:

                try:

                    stored_vector = np.asarray(
                        json.loads(row["vector_json"]),
                        dtype=np.float32
                    )

                    # Validate stored embedding
                    if stored_vector.ndim != 1:
                        invalid_embeddings += 1
                        continue

                    if stored_vector.size != query_vector.size:
                        invalid_embeddings += 1
                        continue

                    if not np.all(np.isfinite(stored_vector)):
                        invalid_embeddings += 1
                        continue

                    stored_norm = np.linalg.norm(stored_vector)

                    if stored_norm == 0:
                        invalid_embeddings += 1
                        continue

                    similarity = float(
                        np.dot(query_vector, stored_vector)
                        / (query_norm * stored_norm)
                    )

                    # Keep cosine similarity within valid bounds
                    similarity = max(
                        -1.0,
                        min(1.0, similarity)
                    )

                    # Apply minimum similarity threshold
                    if similarity < min_similarity:
                        continue

                    results.append({
                        "chunk_id": row["chunk_id"],
                        "document_id": row["document_id"],
                        "filename": row["filename"],
                        "chunk_index": row["chunk_index"],
                        "content": row["content"],
                        "similarity_score": round(
                            similarity, 4
                        )
                    })

                except (
                    ValueError,
                    TypeError,
                    json.JSONDecodeError,
                    OverflowError
                ):

                    invalid_embeddings += 1
                    continue

            # Rank by highest similarity
            results.sort(
                key=lambda item: item["similarity_score"],
                reverse=True
            )

            total_matches = len(results)

            # Return only requested top results
            results = results[:top_k]

            return {
                "success": True,
                "query": query,
                "embedding_model": EMBEDDING_MODEL,
                "top_k": top_k,
                "min_similarity": min_similarity,
                "total_candidates": len(rows),
                "total_matches": total_matches,
                "invalid_embeddings": invalid_embeddings,
                "total_results": len(results),
                "results": results
            }

        finally:

            connection.close()


# Shared semantic search instance
semantic_search = SemanticSearch()