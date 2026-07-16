from typing import Any

from pydantic import BaseModel, Field


class CopilotChatRequest(BaseModel):
    user_id: int
    message: str = Field(min_length=1, max_length=1000)


class CopilotSource(BaseModel):
    source_type: str
    source_id: int | None = None
    title: str | None = None


class CopilotChatResponse(BaseModel):
    user_id: int
    question: str
    intent: str
    answer: str
    data: dict[str, Any]
    suggestions: list[str]
    sources: list[CopilotSource]
    generated_by: str