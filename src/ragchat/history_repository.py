import uuid
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from models import Conversation, Message
from ragchat.constants import MESSAGE_TRIM


def get_or_create_conversation(db: Session, visitor_id: uuid.UUID) -> Conversation:
    conversation = db.scalar(
        select(Conversation).where(Conversation.visitor_id == visitor_id)
    )
    if conversation is None:
        conversation = Conversation(visitor_id=visitor_id)
        db.add(conversation)
        db.flush()
    return conversation


def append_message(
    db: Session,
    visitor_id: uuid.UUID,
    sender: str,
    content: str,
    sources: list[dict[str, Any]] | None = None,
) -> Message:
    conversation = get_or_create_conversation(db, visitor_id)
    message = Message(
        conversation_id=conversation.id,
        sender=sender,
        content=content,
        sources=sources or [],
    )
    db.add(message)
    db.flush()
    _trim_messages(db, conversation.id)
    return message


def get_messages(db: Session, visitor_id: uuid.UUID, limit: int | None = None) -> list[Message]:
    conversation = db.scalar(
        select(Conversation).where(Conversation.visitor_id == visitor_id)
    )
    if conversation is None:
        return []
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
    )
    messages = list(db.scalars(stmt).all())
    if limit is not None:
        return messages[-limit:]
    return messages


def _trim_messages(db: Session, conversation_id: uuid.UUID) -> None:
    count = db.scalar(
        select(func.count()).select_from(Message).where(
            Message.conversation_id == conversation_id
        )
    )
    if count is None or count <= MESSAGE_TRIM:
        return
    overflow = count - MESSAGE_TRIM
    oldest_ids = db.scalars(
        select(Message.id)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .limit(overflow)
    ).all()
    if oldest_ids:
        db.execute(delete(Message).where(Message.id.in_(oldest_ids)))
        db.flush()
