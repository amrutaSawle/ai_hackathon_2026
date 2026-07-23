from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

# Use the same get_db import as your other working routers.
from app.db.database import get_db
from app.schemas.assistant import (
    AssistantChatRequest,
    AssistantChatResponse,
)
from app.services.assistant_service import AssistantService
from app.services.context_resolver import ContextResolver
from app.services.conversation_memory_service import (
    ConversationMemoryService,
)
from app.services.advisor_service import AdvisorService 

router = APIRouter(
    prefix="/api/assistant",
    tags=["AI Assistant"],
)


@router.post(
    "/chat",
    response_model=AssistantChatResponse,
)
def chat_with_assistant(
    request: AssistantChatRequest,
    db: Session = Depends(get_db),
) -> AssistantChatResponse:
    memory_service = ConversationMemoryService(db)
    context_resolver = ContextResolver()

    try:
        last_assistant_message = (
            memory_service.get_last_assistant_message(
                session_id=request.session_id,
                user_id=request.user_id,
            )
        )

        resolved_question = context_resolver.resolve(
            question=request.message,
            last_assistant_message=last_assistant_message,
        )

        memory_service.save_message(
            session_id=request.session_id,
            user_id=request.user_id,
            role="user",
            message=request.message,
            intent=None,
            data={
                "resolved_question": resolved_question,
            },
        )

        assistant_service = AssistantService(db)
        print("=" * 60)
        print("Original :", request.message)
        print("Last assistant :", last_assistant_message)
        print("Resolved :", resolved_question)
        print("=" * 60)
        result = assistant_service.chat(
            user_id=request.user_id,
            message=resolved_question,
        )

        intent = result.get("intent", "UNKNOWN")

        answer = (
            result.get("answer")
            or result.get("message")
            or "I could not generate a response."
        )

        data = result.get("data") or {}
        suggestions = result.get("suggestions") or []
        sources = result.get("sources") or []

        memory_service.save_message(
            session_id=request.session_id,
            user_id=request.user_id,
            role="assistant",
            message=answer,
            intent=intent,
            data=data,
        )

        return AssistantChatResponse(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.message,
            intent=intent,
            answer=answer,
            data=data,
            suggestions=suggestions,
            sources=sources,
            generated_by="finance_copilot",
        )

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Assistant failed to process the request: "
                f"{exc}"
            ),
        ) from exc
from uuid import UUID


@router.get("/sessions/{session_id}/messages")
def get_session_messages(
    session_id: UUID,
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> dict:
    memory_service = ConversationMemoryService(db)

    messages = memory_service.get_recent_messages(
        session_id=session_id,
        user_id=user_id,
        limit=min(limit, 100),
    )

    return {
        "session_id": str(session_id),
        "user_id": user_id,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "message": message.message,
                "intent": message.intent,
                "data": message.data,
                "created_at": message.created_at,
            }
            for message in messages
        ],
    }