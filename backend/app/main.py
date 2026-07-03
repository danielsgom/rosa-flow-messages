import asyncio
import signal
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.modules.logger import get_logger
from app.modules.chat_registry import ChatRegistry
from app.modules.context import PromptLoader, PromptValidator, ConversationHistory, ContextManager
from app.modules.openai_client import OpenRouterClient, ResponseGenerator
from app.modules.photo_registry import PhotoRegistry
from app.modules.telegram import TelegramClientWrapper, MessageEventHandler, TelegramSender
from app.modules.trigger import TriggerEngine
from app.modules.cost_tracker import CostTracker
from app.modules.database import init_db, close_db, UserRepository, ConversationRepository, CostRepository
from app.api.routes import (
    ChatRegistryDep, TelegramClientDep, PhotoRegistryDep, CostTrackerDep,
    ConvRepoDep, CostRepoDep,
    router as api_router,
)
from app.logger_config import setup_logging

logger = get_logger(__name__)

# Global instances
telegram_wrapper: Optional[TelegramClientWrapper] = None
trigger_engine: Optional[TriggerEngine] = None
chat_registry: Optional[ChatRegistry] = None
context_manager: Optional[ContextManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global telegram_wrapper, trigger_engine, chat_registry, context_manager

    settings = get_settings()

    # Setup logging
    setup_logging(settings.log_level)

    # Initialize Database
    session_factory = await init_db(settings.database_url)
    user_repo = UserRepository(session_factory)
    conv_repo = ConversationRepository(session_factory)
    cost_repo = CostRepository(session_factory)
    ConvRepoDep.repo = conv_repo
    CostRepoDep.repo = cost_repo
    logger.info(f"💾 Database initialized: {settings.database_url}")

    # Initialize Chat Registry (with DB repos)
    chat_registry = ChatRegistry(user_repo=user_repo, conv_repo=conv_repo)
    await chat_registry.load_from_db()

    # Direct sqlite3 verification — bypasses SQLAlchemy to confirm actual DB state
    import sqlite3 as _sqlite3
    db_path = Path(settings.database_url.split("///")[-1])
    logger.info(f"💾 DB path: {db_path.resolve()} (exists: {db_path.exists()})")
    if db_path.exists():
        try:
            with _sqlite3.connect(str(db_path.resolve())) as _conn:
                _users = _conn.execute("SELECT chat_id, name, is_vip FROM users").fetchall()
                logger.info(f"💾 sqlite3 direct read: {len(_users)} users in DB → {_users[:5]}")
        except Exception as _e:
            logger.error(f"💾 sqlite3 direct read FAILED: {_e}")
    else:
        logger.warning(f"💾 DB file does NOT exist at {db_path.resolve()}")

    ChatRegistryDep.registry = chat_registry

    # Initialize Context Manager
    prompt_loader = PromptLoader(settings.system_prompt_path)
    examples_loader = PromptLoader(settings.system_prompt_examples_path)
    prompt_validator = PromptValidator(settings.system_prompt_max_tokens)
    history = ConversationHistory()
    context_manager = ContextManager(
        prompt_loader,
        prompt_validator,
        history,
        history_window=settings.context_history_window,
        examples_content=examples_loader.load_optional(),
        heat_detection=settings.conversation_heat_detection,
    )
    context_manager.initialize()

    # Initialize OpenRouter
    openrouter_client = OpenRouterClient(settings.openrouter_api_key)
    cost_tracker = CostTracker(cost_repo=cost_repo)
    CostTrackerDep.tracker = cost_tracker
    generator = ResponseGenerator(
        openrouter_client, settings.openrouter_model, settings.openrouter_max_tokens,
        cost_tracker=cost_tracker,
    )

    # Initialize Telegram
    telegram_wrapper = TelegramClientWrapper(
        api_id=settings.telegram_api_id,
        api_hash=settings.telegram_api_hash,
        session_name=settings.telegram_session_name,
    )

    await telegram_wrapper.start(phone=settings.telegram_phone)
    TelegramClientDep.client = telegram_wrapper

    sender = TelegramSender(telegram_wrapper)

    # Initialize Photo Registry
    photos_dir = Path(settings.photos_dir)
    photo_registry = PhotoRegistry(photos_dir)
    PhotoRegistryDep.registry = photo_registry
    logger.info(f"📸 Photo registry initialized: {photos_dir.resolve()} ({len(photo_registry.list_photos())} photos)")

    # Initialize Trigger Engine
    trigger_engine = TriggerEngine(
        chat_registry=chat_registry,
        context_manager=context_manager,
        generator=generator,
        sender=sender,
        settings=settings,
        photo_registry=photo_registry,
    )

    # Setup message handlers
    event_handler = MessageEventHandler(telegram_wrapper, trigger_engine)
    await event_handler.setup()

    logger.info("🚀 Rosa Flow Messages started successfully!")

    yield

    # Shutdown
    logger.info("Shutting down...")
    if telegram_wrapper:
        await telegram_wrapper.disconnect()
    await close_db()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Rosa Flow Messages",
        description="Automated conversational AI for Telegram",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "rosa-flow-messages"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
