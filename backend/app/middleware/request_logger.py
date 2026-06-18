"""
middleware/request_logger.py
-----------------------------
Starlette BaseHTTPMiddleware that provides two services for every request:

  1. Request-ID propagation:
       - Reads X-Request-ID from the incoming request headers.
       - If absent, generates a fresh UUID4.
       - Injects the ID into the *response* headers as X-Request-ID so
         callers can correlate logs with responses.

  2. Structured request / response logging:
       - Logs method, path, and request_id on the way in.
       - Logs status code, method, path, and duration (ms) on the way out.
       - Uses Python's stdlib logging so the log level and sink are
         controlled by the application's logging configuration.

No I/O other than logging — pure middleware.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Header names (single source of truth)
REQUEST_ID_HEADER = "X-Request-ID"


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Injects X-Request-ID and logs every HTTP transaction.

    Registration (in main.py):
        app.add_middleware(RequestLoggerMiddleware)

    Note: Starlette applies middleware in reverse registration order, so
    this middleware should be registered LAST to be the outermost layer.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # --- Request-ID ---
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())

        # --- Inbound log ---
        t_start = time.perf_counter()
        logger.info(
            "→ [%s] %s %s",
            request_id,
            request.method,
            request.url.path,
        )

        # --- Process ---
        # NOTE: Starlette's BaseHTTPMiddleware re-raises exceptions that escape
        # the inner ExceptionMiddleware before we can set response headers.
        # We catch them here as the outermost safety net so that X-Request-ID
        # is ALWAYS injected — even on unhandled 500 errors.
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            logger.error(
                "Exception escaped inner handlers [%s]: %s",
                request_id,
                exc,
                exc_info=True,
            )
            from fastapi.responses import JSONResponse  # local import avoids circularity
            response = JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "detail": str(exc),
                    "request_id": request_id,
                },
            )

        # --- Outbound log ---
        elapsed_ms = (time.perf_counter() - t_start) * 1000
        logger.info(
            "← [%s] %d %s %s  %.1f ms",
            request_id,
            response.status_code,
            request.method,
            request.url.path,
            elapsed_ms,
        )

        # --- Inject header into response ---
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
