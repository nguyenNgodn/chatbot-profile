import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Visitor


def get_by_email(db: Session, email: str) -> Visitor | None:
    return db.scalar(select(Visitor).where(Visitor.email == email))


def get_by_id(db: Session, visitor_id: uuid.UUID) -> Visitor | None:
    return db.get(Visitor, visitor_id)


def create(db: Session, name: str, email: str) -> Visitor:
    visitor = Visitor(name=name, email=email)
    db.add(visitor)
    db.flush()
    return visitor


def touch(db: Session, visitor: Visitor, name: str) -> Visitor:
    visitor.name = name
    visitor.last_seen_at = datetime.now(timezone.utc)
    db.add(visitor)
    db.flush()
    return visitor
