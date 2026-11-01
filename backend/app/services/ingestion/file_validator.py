"""File validation utilities."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

from app.config import settings
from app.core.exceptions import ValidationError


def validate_file_extension(filename: str) -> str:
    """Return the extension if allowed, else raise ValidationError."""
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type '{ext}' is not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
        )
    return ext


def validate_file_size(file_path: str) -> int:
    """Return file size in bytes, raise ValidationError if too large."""
    size = os.path.getsize(file_path)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size > max_bytes:
        raise ValidationError(
            f"File size {size / 1024 / 1024:.1f} MB exceeds limit of {settings.MAX_UPLOAD_SIZE_MB} MB"
        )
    return size


def sanitize_filename(filename: str) -> str:
    """Remove path traversal characters and sanitize the filename."""
    import re
    # Take only the base name — no directory components
    safe = Path(filename).name
    # Remove any character that isn't alphanumeric, space, dot, dash, or underscore
    safe = re.sub(r"[^\w\s.\-]", "_", safe)
    safe = safe.strip(". ")
    if not safe:
        safe = "upload"
    return safe


def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of file contents."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
