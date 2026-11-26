import uuid
import re
import logging

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from backend.schemas.chat import ChatRequest, ChatResponse

from backend.ai_engine.providers.client import (
    ai_engine,
    AIProviderError
)

from backend.database.connection import get_connection

from backend.rag.rag_service import rag_service


router = APIRouter(tags=["AI Chat"])

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 20


def current_time():
    return datetime.now(timezone.utc).isoformat()


def generate_title(message: str) -> str:

    text = re.sub(r"\s+", " ", message).strip()

    prefixes = [
        "hello aetheriq ai",
        "hello",
        "hi",
        "hey",
        "please",
        "can you",
        "could you",
        "explain",
        "tell me about",
        "what is",
        "what are",
        "help me with",
    ]

    lowered = text.lower()

    for prefix in prefixes:

        if lowered.startswith(prefix):

            text = text[len(prefix):].strip(
                " .,!?-:"
            )

            break

    if not text:
        text = message.strip()

    words = text.split()

    title = " ".join(words[:7])

    if len(words) > 7:
        title += "..."

    return title[:60].strip()


@router.get("/providers")
async def get_providers():

    providers = ai_engine.available_providers()

    return {
        "application": "AETHERIQ AI",
        "available_providers": providers,
        "configured": bool(providers)
    }


@router.post(
    "/chat",
    response_model=ChatResponse
)
async def chat(request: ChatRequest):

    if not request.message.strip():

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    connection = get_connection()

    try:

        conversation_id = request.conversation_id

        # 1. Validate conversation

        if conversation_id:

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
                    detail="Conversation not found."
                )

        else:

            conversation_id = str(uuid.uuid4())

        # 2. Load recent conversation history

        history = []

        if request.conversation_id:

            rows = connection.execute(
                """
                SELECT role, content
                FROM messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    conversation_id,
                    MAX_HISTORY_MESSAGES
                )
            ).fetchall()

            history = [
                {
                    "role": row["role"],
                    "content": row["content"]
                }
                for row in reversed(rows)
            ]

        # 3. Retrieve document context

        rag_result = None

        retrieval_status = "no_matches"

        augmented_message = request.message

        try:

            rag_result = rag_service.prepare_query(
                query=request.message,
                top_k=request.top_k,
                document_id=request.document_id,
                min_similarity=request.min_similarity
            )

            augmented_message = (
                rag_result["augmented_message"]
            )

            retrieval = rag_result.get(
                "retrieval",
                {}
            )

            if retrieval.get("total_results", 0) > 0:

                retrieval_status = "used"

        except Exception:

            logger.exception(
                "RAG retrieval failed."
            )

            retrieval_status = "fallback"

        # 4. Generate AI response

        try:

            result = await ai_engine.generate(
                message=augmented_message,
                preferred_provider=request.provider,
                history=history
            )

        except AIProviderError as error:

            raise HTTPException(
                status_code=503,
                detail=str(error)
            )

        # 5. Create or update conversation

        timestamp = current_time()

        if not request.conversation_id:

            connection.execute(
                """
                INSERT INTO conversations
                (id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    generate_title(request.message),
                    timestamp,
                    timestamp
                )
            )

        else:

            connection.execute(
                """
                UPDATE conversations
                SET updated_at = ?
                WHERE id = ?
                """,
                (
                    timestamp,
                    conversation_id
                )
            )

        # 6. Save user message

        connection.execute(
            """
            INSERT INTO messages
            (conversation_id, role, content,
             provider, model, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                "user",
                request.message,
                None,
                None,
                timestamp
            )
        )

        # 7. Save assistant response

        connection.execute(
            """
            INSERT INTO messages
            (conversation_id, role, content,
             provider, model, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                "assistant",
                result["response"],
                result["provider"],
                result["model"],
                timestamp
            )
        )

        connection.commit()

        retrieval = (
            rag_result.get("retrieval", {})
            if rag_result
            else {}
        )

        sources = retrieval.get(
            "sources",
            []
        )

        retrieved_chunks = retrieval.get(
            "total_results",
            0
        )

        # 8. Return advanced chat response

        return {
            "success": True,
            "application": "AETHERIQ AI",
            "conversation_id": conversation_id,

            **result,

            "rag_used": retrieved_chunks > 0,

            "retrieved_chunks": retrieved_chunks,

            "sources": sources,

            "history_messages_used": len(history),

            "retrieval_status": retrieval_status
        }

    except HTTPException:

        connection.rollback()
        raise

    except Exception:

        connection.rollback()

        logger.exception(
            "AETHERIQ chat request failed."
        )

        raise HTTPException(
            status_code=500,
            detail="An internal chat error occurred."
        )

    finally:

        connection.close()