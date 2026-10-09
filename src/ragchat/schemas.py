import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator


class VisitorIdentifyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name is required")
        return cleaned


class ChatRequest(BaseModel):
    visitor_id: uuid.UUID
    message: str = Field(..., min_length=1, max_length=4000)


class SourceItem(BaseModel):
    source: str
    url: str = ""


class MessageItem(BaseModel):
    sender: str
    content: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime | None = None


class VisitorIdentifyResponse(BaseModel):
    visitor_id: uuid.UUID
    name: str
    email: str
    is_new: bool
    messages: list[MessageItem]


class HistoryResponse(BaseModel):
    messages: list[MessageItem]


class ChatResponse(BaseModel):
    chat_response: str
    sources: list[SourceItem]
