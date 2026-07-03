from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class UserDB(Base):
    __tablename__ = "users"

    chat_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, default="")
    full_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    is_vip = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    auto_enabled = Column(Boolean, nullable=False, default=False)
    # JSON-encoded list of photo filenames assigned to this chat
    assigned_photo_filenames = Column(Text, nullable=False, default="[]")
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    conversations = relationship(
        "ConversationDB", back_populates="user", lazy="select"
    )
    cost_entries = relationship(
        "CostEntryDB", back_populates="user", lazy="select"
    )


class ConversationDB(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(
        Integer, ForeignKey("users.chat_id", ondelete="CASCADE"), nullable=False
    )
    started_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    ended_at = Column(DateTime, nullable=True)
    turn_count = Column(Integer, nullable=False, default=0)
    max_turns = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default="active")

    user = relationship("UserDB", back_populates="conversations")
    photos = relationship(
        "ConversationPhotoDB", back_populates="conversation", lazy="select"
    )
    cost_entries = relationship(
        "CostEntryDB", back_populates="conversation", lazy="select"
    )

    __table_args__ = (
        Index("ix_conversations_chat_id", "chat_id"),
        Index("ix_conversations_status", "status"),
    )


class ConversationPhotoDB(Base):
    __tablename__ = "conversation_photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename = Column(String, nullable=False)
    sent_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    conversation = relationship("ConversationDB", back_populates="photos")


class CostEntryDB(Base):
    __tablename__ = "cost_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(
        Integer, ForeignKey("users.chat_id", ondelete="CASCADE"), nullable=False
    )
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    cost_usd = Column(Float, nullable=False, default=0.0)
    recorded_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("UserDB", back_populates="cost_entries")
    conversation = relationship("ConversationDB", back_populates="cost_entries")

    __table_args__ = (
        Index("ix_cost_entries_chat_id", "chat_id"),
        Index("ix_cost_entries_recorded_at", "recorded_at"),
    )
