import uuid
import sqlite3

from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.database.connection import get_connection, BASE_DIR

from backend.document_engine.document_processor import (
    document_processor
)

from backend.document_engine.loaders.document_loader import (
    DocumentProcessingError
)
from backend.ai_engine.providers.embedding_service import (
    embedding_service
)


router = APIRouter(tags=["Document Intelligence"])


UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024

SUPPORTED_FORMATS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".csv",
    ".txt"
}


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required."
        )

    original_filename = Path(file.filename).name
    extension = Path(original_filename).suffix.lower()

    if extension not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=415,
            detail="Unsupported document format."
        )

    file_bytes = await file.read(MAX_FILE_SIZE + 1)

    await file.close()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the 10 MB upload limit."
        )

    document_id = str(uuid.uuid4())

    stored_filename = f"{document_id}{extension}"

    stored_path = UPLOAD_DIR / stored_filename

    connection = None

    try:

        # Process document
        result = document_processor.process_document(
            file_bytes=file_bytes,
            filename=original_filename
        )

        # Save original uploaded file
        stored_path.write_bytes(file_bytes)

        timestamp = datetime.now(timezone.utc).isoformat()

        connection = get_connection()

        # Save document metadata
        connection.execute(
            """
            INSERT INTO documents (
                id,
                filename,
                stored_filename,
                file_type,
                file_size,
                character_count,
                total_chunks,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                original_filename,
                stored_filename,
                extension,
                len(file_bytes),
                result["metadata"]["character_count"],
                result["metadata"]["total_chunks"],
                timestamp
            )
        )

        # Save document chunks
        for index, chunk in enumerate(result["chunks"], start=1):

            connection.execute(
                """
                INSERT INTO document_chunks (
                    document_id,
                    chunk_index,
                    content,
                    character_count
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    document_id,
                    index,
                    chunk["content"],
                    chunk["character_count"]
                )
            )

        connection.commit()

        # Generate and save AI embeddings
        embedding_result = None
        embedding_error = None

        try:

            embedding_result = embedding_service.embed_document(
                document_id
            )

        except Exception as error:

            embedding_error = str(error)

            print(
                f"EMBEDDING GENERATION FAILED: {embedding_error}"
            )

        return {
            "success": True,
            "embedding_status": (
    "completed"
    if embedding_result
    else "failed"
),
"embedding_result": embedding_result,
"embedding_error": embedding_error,
            "application": "AETHERIQ AI",
            "message": "Document uploaded and stored permanently.",
            "document_id": document_id,
            "filename": original_filename,
            "stored_filename": stored_filename,
            "metadata": result["metadata"],
            "total_chunks_saved": len(result["chunks"]),
            "chunks": result["chunks"],
            "extracted_text": result["extracted_text"]
        }

    except DocumentProcessingError as error:

        if connection:
            connection.rollback()

        if stored_path.exists():
            stored_path.unlink()

        raise HTTPException(
            status_code=422,
            detail=str(error)
        )

    except (OSError, sqlite3.Error) as error:

        if connection:
            connection.rollback()

        if stored_path.exists():
            stored_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Document storage failed: {error}"
        )

    finally:

        if connection:
            connection.close()
# ==========================================
# LIST ALL UPLOADED DOCUMENTS
# ==========================================

@router.get("/documents")
async def list_documents(
    page: int = 1,
    limit: int = 10
):

    if page < 1 or limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Invalid pagination parameters."
        )

    connection = get_connection()

    try:

        total = connection.execute(
            "SELECT COUNT(*) FROM documents"
        ).fetchone()[0]

        offset = (page - 1) * limit

        rows = connection.execute(
            """
            SELECT *
            FROM documents
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        ).fetchall()

        return {
            "success": True,
            "total_documents": total,
            "page": page,
            "limit": limit,
            "documents": [
                dict(row) for row in rows
            ]
        }

    finally:
        connection.close()


# ==========================================
# RETRIEVE DOCUMENT DETAILS AND CHUNKS
# ==========================================

@router.get("/documents/{document_id}")
async def get_document(document_id: str):

    connection = get_connection()

    try:

        document = connection.execute(
            """
            SELECT *
            FROM documents
            WHERE id = ?
            """,
            (document_id,)
        ).fetchone()

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        chunks = connection.execute(
            """
            SELECT chunk_index, content, character_count
            FROM document_chunks
            WHERE document_id = ?
            ORDER BY chunk_index ASC
            """,
            (document_id,)
        ).fetchall()

        return {
            "success": True,
            "document": dict(document),
            "file_exists": (
                UPLOAD_DIR / document["stored_filename"]
            ).is_file(),
            "chunks": [
                dict(chunk) for chunk in chunks
            ]
        }

    finally:
        connection.close()


# ==========================================
# DELETE DOCUMENT
# ==========================================

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):

    connection = get_connection()

    try:

        document = connection.execute(
            """
            SELECT stored_filename
            FROM documents
            WHERE id = ?
            """,
            (document_id,)
        ).fetchone()

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        stored_path = UPLOAD_DIR / document["stored_filename"]

        # Delete metadata and associated chunks.
        # Foreign key cascade removes document_chunks.
        connection.execute(
            """
            DELETE FROM documents
            WHERE id = ?
            """,
            (document_id,)
        )

        connection.commit()

        file_deleted = True

        if stored_path.exists():

            try:
                stored_path.unlink()

            except OSError:
                file_deleted = False

        return {
            "success": True,
            "message": "Document record and chunks deleted.",
            "document_id": document_id,
            "original_file_deleted": file_deleted
        }

    finally:
        connection.close()