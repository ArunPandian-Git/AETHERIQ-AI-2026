import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.database.connection import get_connection


router = APIRouter(tags=["Conversation Management"])


class RenameConversationRequest(BaseModel):

    title: str = Field(
        ...,
        min_length=1,
        max_length=100
    )


def current_time():
    return datetime.now(timezone.utc).isoformat()


# CREATE CONVERSATION

@router.post("/conversations")
async def create_conversation():

    conversation_id = str(uuid.uuid4())
    timestamp = current_time()

    connection = get_connection()

    try:

        connection.execute(
            """
            INSERT INTO conversations
            (id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                conversation_id,
                "New Conversation",
                timestamp,
                timestamp
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Conversation created successfully",
            "conversation": {
                "id": conversation_id,
                "title": "New Conversation",
                "created_at": timestamp,
                "updated_at": timestamp
            }
        }

    finally:
        connection.close()


# GET ALL CONVERSATIONS WITH PAGINATION

@router.get("/conversations")
async def get_conversations(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):

    connection = get_connection()

    try:

        offset = (page - 1) * limit

        total = connection.execute(
            """
            SELECT COUNT(*)
            FROM conversations
            """
        ).fetchone()[0]

        rows = connection.execute(
            """
            SELECT *
            FROM conversations
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        ).fetchall()

        total_pages = (
            (total + limit - 1) // limit
        )

        return {
            "success": True,
            "pagination": {
                "current_page": page,
                "per_page": limit,
                "total_conversations": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            },
            "conversations": [
                dict(row) for row in rows
            ]
        }

    finally:
        connection.close()
# SEARCH CONVERSATIONS

@router.get("/conversations/search")
async def search_conversations(
    q: str = Query(..., min_length=1, max_length=100)
):

    connection = get_connection()

    try:

        search_term = f"%{q.strip()}%"

        rows = connection.execute(
            """
            SELECT *
            FROM conversations
            WHERE title LIKE ?
            ORDER BY updated_at DESC
            """,
            (search_term,)
        ).fetchall()

        return {
            "success": True,
            "search_query": q,
            "total": len(rows),
            "conversations": [
                dict(row) for row in rows
            ]
        }

    finally:
        connection.close()

# GET SINGLE CONVERSATION

@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):

    connection = get_connection()

    try:

        conversation = connection.execute(
            """
            SELECT *
            FROM conversations
            WHERE id = ?
            """,
            (conversation_id,)
        ).fetchone()

        if conversation is None:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

        messages = connection.execute(
            """
            SELECT *
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,)
        ).fetchall()

        return {
            "success": True,
            "conversation": dict(conversation),
            "messages": [
                dict(message) for message in messages
            ]
        }

    finally:
        connection.close()


# RENAME CONVERSATION

@router.put("/conversations/{conversation_id}")
async def rename_conversation(
    conversation_id: str,
    request: RenameConversationRequest
):

    connection = get_connection()

    try:

        conversation = connection.execute(
            """
            SELECT id
            FROM conversations
            WHERE id = ?
            """,
            (conversation_id,)
        ).fetchone()

        if conversation is None:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

        connection.execute(
            """
            UPDATE conversations
            SET title = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                request.title.strip(),
                current_time(),
                conversation_id
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Conversation renamed successfully",
            "conversation_id": conversation_id,
            "new_title": request.title.strip()
        }

    finally:
        connection.close()


# DELETE CONVERSATION

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):

    connection = get_connection()

    try:

        cursor = connection.execute(
            """
            DELETE FROM conversations
            WHERE id = ?
            """,
            (conversation_id,)
        )

        connection.commit()

        if cursor.rowcount == 0:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

        return {
            "success": True,
            "message": "Conversation deleted successfully",
            "conversation_id": conversation_id
        }

    finally:
        connection.close()