from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AssistantChatRequest(BaseModel):
    user_id: int = Field(gt=0)
    session_id: UUID
    message: str = Field(min_length=1, max_length=500)


class AssistantChatResponse(BaseModel):
    user_id: int
    session_id: UUID
    intent: str

    # Original user message
    message: str

    # Assistant response
    answer: str

    data: dict[str, Any] | None = None
    suggestions: list[str] = []
    sources: list[Any] = []

    generated_by: str = "finance_copilot"