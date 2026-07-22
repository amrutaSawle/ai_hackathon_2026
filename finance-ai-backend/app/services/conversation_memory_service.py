from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.conversation_message import ConversationMessage


class ConversationMemoryService:
    def __init__(self, db: Session):
        self.db = db

    def save_message(
        self,
        *,
        session_id: UUID,
        user_id: int,
        role: str,
        message: str,
        intent: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        record = ConversationMessage(
            session_id=session_id,
            user_id=user_id,
            role=role,
            message=message,
            intent=intent,
            data=data or {},
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return record

    def get_recent_messages(
        self,
        *,
        session_id: UUID,
        user_id: int,
        limit: int = 10,
    ) -> list[ConversationMessage]:
        messages = (
            self.db.query(ConversationMessage)
            .filter(
                ConversationMessage.session_id == session_id,
                ConversationMessage.user_id == user_id,
            )
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
            .all()
        )

        return list(reversed(messages))

    def get_last_assistant_message(
        self,
        *,
        session_id: UUID,
        user_id: int,
    ) -> ConversationMessage | None:
        return (
            self.db.query(ConversationMessage)
            .filter(
                ConversationMessage.session_id == session_id,
                ConversationMessage.user_id == user_id,
                ConversationMessage.role == "assistant",
            )
            .order_by(ConversationMessage.created_at.desc())
            .first()
        )

    def clear_session(
        self,
        *,
        session_id: UUID,
        user_id: int,
    ) -> int:
        deleted_count = (
            self.db.query(ConversationMessage)
            .filter(
                ConversationMessage.session_id == session_id,
                ConversationMessage.user_id == user_id,
            )
            .delete(synchronize_session=False)
        )

        self.db.commit()

        return deleted_count