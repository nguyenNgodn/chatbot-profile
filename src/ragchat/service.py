import uuid
from typing import Any

from sqlalchemy.orm import Session

from models import Message
from ragchat import history_repository, visitors_repository
from ragchat.constants import CHATBOT_FIRST_MESSAGE, HISTORY_FOR_PROMPT
from ragchat.exceptions import VisitorNotFound
from ragchat.identity import normalize_email
from ragchat.prompt_templates import RagPrompt


def _message_item(message: Message) -> dict[str, Any]:
    return {
        "sender": message.sender,
        "content": message.content,
        "sources": message.sources or [],
        "created_at": message.created_at,
    }


def identify_visitor(db: Session, name: str, email: str) -> dict[str, Any]:
    normalized = normalize_email(email)
    visitor = visitors_repository.get_by_email(db, normalized)
    is_new = visitor is None
    if visitor is None:
        visitor = visitors_repository.create(db, name=name.strip(), email=normalized)
        history_repository.get_or_create_conversation(db, visitor.id)
        messages: list[dict[str, Any]] = []
    else:
        visitors_repository.touch(db, visitor, name=name.strip())
        messages = [_message_item(item) for item in history_repository.get_messages(db, visitor.id)]
    return {
        "visitor_id": visitor.id,
        "name": visitor.name,
        "email": visitor.email,
        "is_new": is_new,
        "messages": messages,
    }


def get_history(db: Session, visitor_id: uuid.UUID, include_welcome: bool = False) -> dict[str, Any]:
    if visitors_repository.get_by_id(db, visitor_id) is None:
        raise VisitorNotFound()
    messages = [_message_item(item) for item in history_repository.get_messages(db, visitor_id)]
    if include_welcome:
        messages = [
            {
                "sender": "chatbot",
                "content": CHATBOT_FIRST_MESSAGE,
                "sources": [],
                "created_at": None,
            },
            *messages,
        ]
    return {"messages": messages}


def answer_chat(db: Session, visitor_id: uuid.UUID, chat_message: str) -> dict[str, Any]:
    if visitors_repository.get_by_id(db, visitor_id) is None:
        raise VisitorNotFound()

    from ragchat.llm import generate_answer
    from ragchat.rag_engine import retrieve

    history_repository.append_message(db, visitor_id, sender="user", content=chat_message)
    chunks = retrieve(chat_message, top_k=5)
    context = "\n\n".join(chunk["text"] for chunk in chunks if chunk.get("text"))
    prior = history_repository.get_messages(db, visitor_id, limit=HISTORY_FOR_PROMPT + 1)
    history_for_prompt = [
        {"sender": item.sender, "content": item.content} for item in prior[:-1][-HISTORY_FOR_PROMPT:]
    ]
    prompt = RagPrompt.build(context=context, history=history_for_prompt, question=chat_message)
    answer = generate_answer(prompt)

    seen: set[tuple[str, str]] = set()
    sources: list[dict[str, str]] = []
    for chunk in chunks:
        pair = (chunk.get("source") or "", chunk.get("url") or "")
        if pair in seen:
            continue
        seen.add(pair)
        sources.append({"source": pair[0], "url": pair[1]})

    history_repository.append_message(
        db, visitor_id, sender="chatbot", content=answer, sources=sources
    )
    return {"chat_response": answer, "sources": sources}


def clear_all() -> dict[str, str]:
    from ragchat.llm import clear_llm_cache
    from ragchat.rag_engine import clear_retrieval_cache

    clear_retrieval_cache()
    clear_llm_cache()
    return {"status": "ok"}
