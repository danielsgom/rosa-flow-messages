import asyncio
from collections import defaultdict
from typing import List, Dict, Optional, TYPE_CHECKING

from app.modules.logger import get_logger
from .models import CostEntry, CostSummary, ChatCostSummary

if TYPE_CHECKING:
    from app.modules.database.repositories import CostRepository

logger = get_logger(__name__)

# DeepSeek deepseek-chat pricing (USD per 1M tokens)
_INPUT_PRICE_PER_M = 0.27
_OUTPUT_PRICE_PER_M = 1.10

_MAX_ENTRIES = 1000  # in-memory fallback limit


class CostTracker:
    """Tracks LLM API usage and cost per conversation.

    When a CostRepository is provided, all data is persisted to the DB.
    Without it, falls back to in-memory storage (useful in tests).
    """

    def __init__(
        self,
        input_price_per_m: float = _INPUT_PRICE_PER_M,
        output_price_per_m: float = _OUTPUT_PRICE_PER_M,
        cost_repo: Optional["CostRepository"] = None,
    ):
        self._entries: List[CostEntry] = []  # in-memory fallback
        self._lock = asyncio.Lock()
        self._input_price = input_price_per_m
        self._output_price = output_price_per_m
        self._cost_repo = cost_repo

    def _calc_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return (
            prompt_tokens * self._input_price / 1_000_000
            + completion_tokens * self._output_price / 1_000_000
        )

    async def record(
        self,
        chat_id: int,
        chat_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        conversation_id: Optional[int] = None,
    ) -> CostEntry:
        cost = self._calc_cost(prompt_tokens, completion_tokens)
        entry = CostEntry(
            chat_id=chat_id,
            chat_name=chat_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
        )

        if self._cost_repo is not None:
            await self._cost_repo.record(
                chat_id, conversation_id, prompt_tokens, completion_tokens, cost
            )
        else:
            async with self._lock:
                self._entries.append(entry)
                if len(self._entries) > _MAX_ENTRIES:
                    self._entries = self._entries[-_MAX_ENTRIES:]

        logger.debug(
            f"💰 Cost recorded: chat={chat_id} conv={conversation_id} "
            f"in={prompt_tokens} out={completion_tokens} ${cost:.6f}"
        )
        return entry

    async def get_summary(self) -> CostSummary:
        if self._cost_repo is not None:
            data = await self._cost_repo.summary_global()
            return CostSummary(**data)

        async with self._lock:
            entries = list(self._entries)
        prompt = sum(e.prompt_tokens for e in entries)
        completion = sum(e.completion_tokens for e in entries)
        return CostSummary(
            total_calls=len(entries),
            total_prompt_tokens=prompt,
            total_completion_tokens=completion,
            total_tokens=prompt + completion,
            total_cost_usd=sum(e.cost_usd for e in entries),
        )

    async def get_by_chat(self) -> List[ChatCostSummary]:
        if self._cost_repo is not None:
            rows = await self._cost_repo.summary_by_chat()
            return [ChatCostSummary(**r) for r in rows]

        async with self._lock:
            entries = list(self._entries)

        agg: Dict[int, dict] = defaultdict(lambda: {
            "chat_name": "", "calls": 0, "prompt_tokens": 0,
            "completion_tokens": 0, "cost_usd": 0.0,
        })
        for e in entries:
            d = agg[e.chat_id]
            d["chat_name"] = e.chat_name
            d["calls"] += 1
            d["prompt_tokens"] += e.prompt_tokens
            d["completion_tokens"] += e.completion_tokens
            d["cost_usd"] += e.cost_usd

        return sorted(
            [
                ChatCostSummary(
                    chat_id=cid,
                    chat_name=d["chat_name"],
                    calls=d["calls"],
                    prompt_tokens=d["prompt_tokens"],
                    completion_tokens=d["completion_tokens"],
                    total_tokens=d["prompt_tokens"] + d["completion_tokens"],
                    cost_usd=d["cost_usd"],
                )
                for cid, d in agg.items()
            ],
            key=lambda x: x.cost_usd,
            reverse=True,
        )

    async def get_recent(self, n: int = 50) -> List[CostEntry]:
        if self._cost_repo is not None:
            rows = await self._cost_repo.recent(n)
            return [CostEntry(**r) for r in rows]

        async with self._lock:
            return list(reversed(self._entries[-n:]))
