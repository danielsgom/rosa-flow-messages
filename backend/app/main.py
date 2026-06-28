import asyncio
import signal
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.modules.logger import get_logger
from app.modules.chat_registry import ChatRegistry
from app.modules.context import PromptLoader, PromptValidator, ConversationHistory, ContextManager
from app.modules.openai_client import OpenAIClient, ResponseGenerator
from app.modules.telegram import TelegramClientWrapper, MessageEventHandler, TelegramSender
from app.modules.trigger import TriggerEngine
from app.api.routes import ChatRegistryDep, TelegramClientDep, router as api_router
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
    prompt_validator = PromptValidator(settings.system_prompt_max_tokens)
    history = ConversationHistory()
    context_manager = ContextManager(prompt_loader, prompt_validator, history)
    context_manager.initialize()

    # Initialize OpenAI
    openai_client = OpenAIClient(settings.openai_api_key)
    generator = ResponseGenerator(openai_client, settings.openai_model)

    # Initialize Telegram
    telegram_wrapper = TelegramClientWrapper(
        api_id=settings.telegram_api_id,
        api_hash=settings.telegram_api_hash,
        session_name=settings.telegram_session_name,
    )

    await telegram_wrapper.start(phone=settings.telegram_phone)
    TelegramClientDep.client = telegram_wrapper

    sender = TelegramSender(telegram_wrapper)

    # Initialize Trigger Engine
    trigger_engine = TriggerEngine(
        chat_registry=chat_registry,
        context_manager=context_manager,
        generator=generator,
        sender=sender,
        settings=settings,
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
