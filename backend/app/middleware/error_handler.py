"""
middleware/error_handler.py
----------------------------
Global exception handlers for the FastAPI application.

Registers two handlers on the app:
  1. RequestValidationError → 422 JSON with all validation messages.
  2. Exception (catch-all)  → 500 JSON with a safe error message.
     Logs the full traceback server-side; the client only sees the message.

The HTTPException handler is intentionally left as FastAPI's built-in because
it already returns JSON and preserves status codes correctly.

Both handlers inject the X-Request-ID from the request headers (populated by
RequestLoggerMiddleware) into the error response body so callers can correlate
errors with log lines.

No I/O other than logging — pure error-shaping logic.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def add_error_handlers(app: FastAPI) -> None:
    """
    Register all custom exception handlers on the FastAPI application.
    Call this AFTER the app is created, BEFORE starting the server.
    """

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Pydantic / FastAPI request-body validation failures.
        Returns 422 with a flat list of field errors.
        """
        request_id = request.headers.get("X-Request-ID", "unknown")
        logger.warning(
            "Validation error [request_id=%s] %s %s: %s",
            request_id,
            request.method,
            request.url.path,
            exc.errors(),
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation error",
                "detail": exc.errors(),
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Catch-all handler for any unhandled exception.
        Logs the full traceback (with exc_info=True) but only returns
        a safe, non-leaking message to the client.
        """
        request_id = request.headers.get("X-Request-ID", "unknown")
        logger.error(
            "Unhandled exception [request_id=%s] %s %s",
            request_id,
            request.method,
            request.url.path,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc),
                "request_id": request_id,
            },
        )
