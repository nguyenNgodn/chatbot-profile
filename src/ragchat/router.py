import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from config import settings
from db import get_db
from ragchat import rag_engine, service
from ragchat.exceptions import VisitorNotFound
from ragchat.schemas import (
    ChatRequest,
    ChatResponse,
    HistoryResponse,
    VisitorIdentifyRequest,
    VisitorIdentifyResponse,
)

router = APIRouter()


def _require_secret(x_secret_key: str | None = Header(default=None, alias="X-Secret-Key")) -> None:
    if not x_secret_key or x_secret_key != settings.SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid secret key")


@router.post("/visitor", response_model=VisitorIdentifyResponse)
def identify_visitor(payload: VisitorIdentifyRequest, db: Session = Depends(get_db)):
    return service.identify_visitor(db, name=payload.name, email=str(payload.email))


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    try:
        return service.answer_chat(db, payload.visitor_id, payload.message)
    except VisitorNotFound as exc:
        raise HTTPException(status_code=404, detail="Visitor not found") from exc


@router.get("/history", response_model=HistoryResponse)
def history(
    visitor_id: uuid.UUID | None = Query(default=None),
    include_welcome: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    if visitor_id is None:
        raise HTTPException(status_code=400, detail="visitor_id is required")
    try:
        return service.get_history(db, visitor_id, include_welcome=include_welcome)
    except VisitorNotFound as exc:
        raise HTTPException(status_code=404, detail="Visitor not found") from exc


@router.post("/clear")
def clear(_: None = Depends(_require_secret)):
    return service.clear_all()


@router.post("/reingest")
def reingest(_: None = Depends(_require_secret)):
    return rag_engine.reingest()
