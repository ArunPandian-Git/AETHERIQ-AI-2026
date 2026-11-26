from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):

    message: str = Field(
        ...,
        min_length=1,
        max_length=12000
    )

    provider: Optional[str] = None

    conversation_id: Optional[str] = None

    # Optional document-specific RAG
    document_id: Optional[str] = None

    # Retrieval controls
    top_k: int = Field(
        default=5,
        ge=1,
        le=20
    )

    min_similarity: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0
    )


class ChatResponse(BaseModel):

    success: bool

    application: str

    conversation_id: str

    provider: str

    model: str

    response: str

    rag_used: bool = False

    retrieved_chunks: int = 0

    sources: list[dict[str, Any]] = Field(
        default_factory=list
    )

    history_messages_used: int = 0

    retrieval_status: str = "no_matches"