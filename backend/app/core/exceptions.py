"""Custom exception hierarchy and FastAPI exception handlers."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class PlaceholderError(Exception):
    """Base application exception."""

    status_code: int = 500

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        super().__init__(message)


class NotFoundError(PlaceholderError):
    status_code = 404


class ValidationError(PlaceholderError):
    status_code = 422


class IngestionError(PlaceholderError):
    status_code = 500


class RetrievalError(PlaceholderError):
    status_code = 500


class ExtractionError(PlaceholderError):
    status_code = 500


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PlaceholderError)
    async def placeholder_error_handler(request: Request, exc: PlaceholderError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "error": type(exc).__name__},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred.", "error": type(exc).__name__},
        )
