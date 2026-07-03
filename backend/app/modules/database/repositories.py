import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.logger import get_logger
from .models import ConversationDB, ConversationPhotoDB, CostEntryDB, UserDB

logger = get_logger(__name__)


class UserRepository:
    """Persistent storage for user / chat metadata."""

    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._sf = session_factory

    async def upsert(
        self,
        chat_id: int,
        name: str = "",
        full_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> UserDB:
        """Insert a new user or update name/full_name/username for an existing one.
        Uses SQLite INSERT OR IGNORE + SELECT to be race-condition safe.
        Never overwrites is_vip or auto_enabled (use dedicated setters for those)."""
        now = datetime.now(timezone.utc)
        async with self._sf() as session:
            # Atomic insert — silently ignored if chat_id already exists
            stmt = (
                sqlite_insert(UserDB)
                .values(
                    chat_id=chat_id,
                    name=name or str(chat_id),
                    full_name=full_name,
                    username=username,
                    created_at=now,
                    updated_at=now,
                )
                .prefix_with("OR IGNORE")
            )
            result = await session.execute(stmt)
            is_new = result.rowcount == 1

            if is_new:
                await session.commit()
                logger.info(f"💾 upsert: NEW user {chat_id} ({name}) inserted")
            else:
                # Row existed — update mutable fields only
                user = await session.get(UserDB, chat_id)
                if user is not None:
                    if name:
                        user.name = name
                    if full_name:
                        user.full_name = full_name
                    if username:
                        user.username = username
                    user.updated_at = now
                    await session.commit()

            user = await session.get(UserDB, chat_id)
            return user

    async def set_vip(self, chat_id: int, is_vip: bool) -> Optional[UserDB]:
        async with self._sf() as session:
            user = await session.get(UserDB, chat_id)
            if user is None:
                return None
            user.is_vip = is_vip
            user.updated_at = datetime.now(timezone.utc)
            await session.commit()
            return user

    async def set_auto_enabled(self, chat_id: int, enabled: bool) -> Optional[UserDB]:
        async with self._sf() as session:
            user = await session.get(UserDB, chat_id)
            if user is None:
                return None
            user.auto_enabled = enabled
            user.updated_at = datetime.now(timezone.utc)
            await session.commit()
            return user

    async def set_assigned_photos(
        self, chat_id: int, filenames: List[str]
    ) -> Optional[UserDB]:
        async with self._sf() as session:
            user = await session.get(UserDB, chat_id)
            if user is None:
                return None
            user.assigned_photo_filenames = json.dumps(filenames)
            user.updated_at = datetime.now(timezone.utc)
            await session.commit()
            return user

    async def get(self, chat_id: int) -> Optional[UserDB]:
        async with self._sf() as session:
            return await session.get(UserDB, chat_id)

    async def get_all(self) -> List[UserDB]:
        async with self._sf() as session:
            result = await session.execute(select(UserDB))
            return list(result.scalars().all())


class ConversationRepository:
    """Persistent storage for conversation sessions."""

    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._sf = session_factory

    async def start(self, chat_id: int, max_turns: int) -> int:
        """Create a new active conversation record. Returns its DB id."""
        async with self._sf() as session:
            conv = ConversationDB(
                chat_id=chat_id,
                max_turns=max_turns,
                status="active",
            )
            session.add(conv)
            await session.commit()
            await session.refresh(conv)
            return conv.id

    async def close(self, conv_id: int, turn_count: int) -> None:
        """Mark a conversation as closed."""
        async with self._sf() as session:
            conv = await session.get(ConversationDB, conv_id)
            if conv:
                conv.ended_at = datetime.now(timezone.utc)
                conv.turn_count = turn_count
                conv.status = "closed"
                await session.commit()

    async def get_active(self, chat_id: int) -> Optional[ConversationDB]:
        """Return the most recent active conversation for a chat, or None."""
        async with self._sf() as session:
            result = await session.execute(
                select(ConversationDB)
                .where(ConversationDB.chat_id == chat_id)
                .where(ConversationDB.status == "active")
                .order_by(ConversationDB.started_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def count_by_chat(self, chat_id: int) -> int:
        async with self._sf() as session:
            result = await session.execute(
                select(func.count())
                .select_from(ConversationDB)
                .where(ConversationDB.chat_id == chat_id)
            )
            return result.scalar() or 0

    async def count_all_by_chat(self) -> Dict[int, int]:
        """Return a mapping {chat_id: total_conversations} for all chats."""
        async with self._sf() as session:
            result = await session.execute(
                select(ConversationDB.chat_id, func.count().label("cnt")).group_by(
                    ConversationDB.chat_id
                )
            )
            return {row.chat_id: row.cnt for row in result.all()}

    async def add_photo(self, conv_id: int, filename: str) -> None:
        async with self._sf() as session:
            photo = ConversationPhotoDB(conversation_id=conv_id, filename=filename)
            session.add(photo)
            await session.commit()

    async def get_photos(self, conv_id: int) -> List[str]:
        async with self._sf() as session:
            result = await session.execute(
                select(ConversationPhotoDB.filename)
                .where(ConversationPhotoDB.conversation_id == conv_id)
                .order_by(ConversationPhotoDB.sent_at)
            )
            return list(result.scalars().all())

    async def list_by_chat(self, chat_id: int) -> List[ConversationDB]:
        async with self._sf() as session:
            result = await session.execute(
                select(ConversationDB)
                .where(ConversationDB.chat_id == chat_id)
                .order_by(ConversationDB.started_at.desc())
            )
            return list(result.scalars().all())


class CostRepository:
    """Persistent storage for LLM API cost entries."""

    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._sf = session_factory

    async def record(
        self,
        chat_id: int,
        conversation_id: Optional[int],
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
    ) -> None:
        async with self._sf() as session:
            entry = CostEntryDB(
                chat_id=chat_id,
                conversation_id=conversation_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost_usd,
            )
            session.add(entry)
            await session.commit()

    async def summary_global(self) -> dict:
        async with self._sf() as session:
            result = await session.execute(
                select(
                    func.count().label("calls"),
                    func.sum(CostEntryDB.prompt_tokens).label("prompt_tokens"),
                    func.sum(CostEntryDB.completion_tokens).label("completion_tokens"),
                    func.sum(CostEntryDB.cost_usd).label("cost_usd"),
                )
            )
            row = result.one()
            return {
                "total_calls": row.calls or 0,
                "total_prompt_tokens": row.prompt_tokens or 0,
                "total_completion_tokens": row.completion_tokens or 0,
                "total_tokens": (row.prompt_tokens or 0) + (row.completion_tokens or 0),
                "total_cost_usd": row.cost_usd or 0.0,
            }

    async def summary_by_chat(self) -> List[dict]:
        async with self._sf() as session:
            result = await session.execute(
                select(
                    CostEntryDB.chat_id,
                    UserDB.name.label("chat_name"),
                    func.count().label("calls"),
                    func.sum(CostEntryDB.prompt_tokens).label("prompt_tokens"),
                    func.sum(CostEntryDB.completion_tokens).label("completion_tokens"),
                    func.sum(CostEntryDB.cost_usd).label("cost_usd"),
                )
                .outerjoin(UserDB, UserDB.chat_id == CostEntryDB.chat_id)
                .group_by(CostEntryDB.chat_id)
                .order_by(func.sum(CostEntryDB.cost_usd).desc())
            )
            return [
                {
                    "chat_id": r.chat_id,
                    "chat_name": r.chat_name or str(r.chat_id),
                    "calls": r.calls,
                    "prompt_tokens": r.prompt_tokens or 0,
                    "completion_tokens": r.completion_tokens or 0,
                    "total_tokens": (r.prompt_tokens or 0) + (r.completion_tokens or 0),
                    "cost_usd": r.cost_usd or 0.0,
                }
                for r in result.all()
            ]

    async def total_by_chat(self, chat_id: int) -> float:
        async with self._sf() as session:
            result = await session.execute(
                select(func.sum(CostEntryDB.cost_usd)).where(
                    CostEntryDB.chat_id == chat_id
                )
            )
            return result.scalar() or 0.0

    async def total_all_by_chat(self) -> Dict[int, float]:
        """Return a mapping {chat_id: total_cost_usd} for all chats."""
        async with self._sf() as session:
            result = await session.execute(
                select(
                    CostEntryDB.chat_id,
                    func.sum(CostEntryDB.cost_usd).label("total"),
                ).group_by(CostEntryDB.chat_id)
            )
            return {row.chat_id: row.total or 0.0 for row in result.all()}

    async def total_by_conversation(self, conv_id: int) -> float:
        async with self._sf() as session:
            result = await session.execute(
                select(func.sum(CostEntryDB.cost_usd)).where(
                    CostEntryDB.conversation_id == conv_id
                )
            )
            return result.scalar() or 0.0

    async def recent(self, n: int = 50) -> List[dict]:
        """Return the n most recent cost entries with chat name resolved."""
        async with self._sf() as session:
            result = await session.execute(
                select(
                    CostEntryDB.chat_id,
                    UserDB.name.label("chat_name"),
                    CostEntryDB.prompt_tokens,
                    CostEntryDB.completion_tokens,
                    CostEntryDB.cost_usd,
                    CostEntryDB.recorded_at,
                )
                .outerjoin(UserDB, UserDB.chat_id == CostEntryDB.chat_id)
                .order_by(CostEntryDB.recorded_at.desc())
                .limit(n)
            )
            return [
                {
                    "chat_id": r.chat_id,
                    "chat_name": r.chat_name or str(r.chat_id),
                    "prompt_tokens": r.prompt_tokens,
                    "completion_tokens": r.completion_tokens,
                    "cost_usd": r.cost_usd,
                    "timestamp": r.recorded_at,
                }
                for r in result.all()
            ]
