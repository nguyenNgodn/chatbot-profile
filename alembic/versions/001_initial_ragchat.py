"""initial ragchat visitors, conversations, messages

Revision ID: 001_initial
Revises:
Create Date: 2026-09-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ragchat_visitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_ragchat_visitors_email", "ragchat_visitors", ["email"], unique=True)

    op.create_table(
        "ragchat_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("visitor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["visitor_id"], ["ragchat_visitors.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("visitor_id"),
    )
    op.create_index(
        "ix_ragchat_conversations_visitor_id",
        "ragchat_conversations",
        ["visitor_id"],
        unique=True,
    )

    op.create_table(
        "ragchat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["ragchat_conversations.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_ragchat_messages_conversation_id",
        "ragchat_messages",
        ["conversation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ragchat_messages_conversation_id", table_name="ragchat_messages")
    op.drop_table("ragchat_messages")
    op.drop_index("ix_ragchat_conversations_visitor_id", table_name="ragchat_conversations")
    op.drop_table("ragchat_conversations")
    op.drop_index("ix_ragchat_visitors_email", table_name="ragchat_visitors")
    op.drop_table("ragchat_visitors")
