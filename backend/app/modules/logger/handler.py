from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .logger import get_logger
from .exceptions import RosaFlowError

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware for FastAPI."""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except RosaFlowError as exc:
            logger.error(f"Application error: {exc.__class__.__name__}: {str(exc)}")
            return JSONResponse(
                status_code=400,
                content={"detail": str(exc), "error_type": exc.__class__.__name__},
            )
        except Exception as exc:
            logger.error(f"Unhandled error: {exc.__class__.__name__}: {str(exc)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "error_type": "InternalError"},
            )
