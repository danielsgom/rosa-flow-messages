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
from app.api.routes import ChatRegistryDep, TelegramClientDep, PhotoRegistryDep, router as api_router
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

    # Initialize Chat Registry
    chat_registry = ChatRegistry()
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
    generator = ResponseGenerator(openrouter_client, settings.openrouter_model, settings.openrouter_max_tokens)

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
