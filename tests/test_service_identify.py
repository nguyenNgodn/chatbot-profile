import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from ragchat.exceptions import VisitorNotFound
from ragchat.service import get_history, identify_visitor


def test_identify_creates_new_visitor():
    db = MagicMock()
    visitor = SimpleNamespace(
        id=uuid.uuid4(), name="An", email="an@example.com"
    )
    with (
        patch("ragchat.service.visitors_repository") as visitors,
        patch("ragchat.service.history_repository") as history,
    ):
        visitors.get_by_email.return_value = None
        visitors.create.return_value = visitor
        result = identify_visitor(db, name="An", email="An@Example.com")

    visitors.get_by_email.assert_called_once_with(db, "an@example.com")
    visitors.create.assert_called_once()
    history.get_or_create_conversation.assert_called_once_with(db, visitor.id)
    assert result["is_new"] is True
    assert result["messages"] == []
    assert result["email"] == "an@example.com"


def test_identify_returns_history_for_existing_visitor():
    db = MagicMock()
    visitor_id = uuid.uuid4()
    visitor = SimpleNamespace(id=visitor_id, name="An", email="an@example.com")
    prior = SimpleNamespace(
        sender="user", content="hi", sources=[], created_at=None
    )
    with (
        patch("ragchat.service.visitors_repository") as visitors,
        patch("ragchat.service.history_repository") as history,
    ):
        visitors.get_by_email.return_value = visitor
        history.get_messages.return_value = [prior]
        result = identify_visitor(db, name="Anh", email="an@example.com")

    visitors.touch.assert_called_once()
    assert result["is_new"] is False
    assert result["messages"][0]["content"] == "hi"


def test_get_history_missing_visitor():
    db = MagicMock()
    with patch("ragchat.service.visitors_repository") as visitors:
        visitors.get_by_id.return_value = None
        try:
            get_history(db, uuid.uuid4())
        except VisitorNotFound:
            return
        raise AssertionError("expected VisitorNotFound")
