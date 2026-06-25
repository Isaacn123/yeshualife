"""Backblaze B2 upload helpers."""

from __future__ import annotations

import re
from pathlib import Path


def safe_upload_filename(filename: str) -> str:
    """Use URL-safe object names (no spaces) for fewer playback issues."""
    name = Path((filename or "").strip()).name
    if not name:
        return "video.mp4"
    stem = Path(name).stem
    ext = Path(name).suffix.lower()
    if ext not in {".mp4", ".mov", ".m4v", ".webm"}:
        ext = ".mp4"
    safe_stem = re.sub(r"[^\w\-]+", "-", stem).strip("-").lower() or "video"
    return f"{safe_stem}{ext}"
