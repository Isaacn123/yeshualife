"""Generate video poster images and metadata via ffmpeg/ffprobe."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings

from .b2 import b2_presigned_get_url, b2_public_url, get_b2_config, get_b2_s3_client


class FFmpegNotFoundError(FileNotFoundError):
    """Raised when ffmpeg cannot be located."""


def _bundled_ffmpeg() -> str | None:
    """Pip package imageio-ffmpeg ships a static ffmpeg binary (no apt install)."""
    try:
        import imageio_ffmpeg

        path = imageio_ffmpeg.get_ffmpeg_exe()
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    except Exception:
        pass
    return None


def _resolve_ffmpeg() -> str:
    configured = (os.environ.get("FFMPEG_BIN") or getattr(settings, "FFMPEG_BIN", "") or "").strip()
    if configured:
        return configured
    found = shutil.which("ffmpeg")
    if found:
        return found
    for candidate in ("/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    bundled = _bundled_ffmpeg()
    if bundled:
        return bundled
    raise FFmpegNotFoundError(
        "ffmpeg not found. Either: (1) `sudo apt install -y ffmpeg`, or "
        "(2) `pip install imageio-ffmpeg` in your venv, or "
        "(3) set FFMPEG_BIN=/full/path/to/ffmpeg"
    )


def _resolve_ffprobe() -> str | None:
    """ffprobe is optional; duration can be parsed via ffmpeg if missing."""
    configured = (os.environ.get("FFPROBE_BIN") or getattr(settings, "FFPROBE_BIN", "") or "").strip()
    if configured:
        return configured
    found = shutil.which("ffprobe")
    if found:
        return found
    for candidate in ("/usr/bin/ffprobe", "/usr/local/bin/ffprobe"):
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def ensure_ffmpeg_available() -> str:
    """Return ffmpeg path or raise FFmpegNotFoundError."""
    return _resolve_ffmpeg()


def poster_url_for_key(key: str) -> str:
    """Stable-enough URL for <img> tags (public CDN path preferred)."""
    if getattr(settings, "B2_POSTER_USE_PRESIGNED", False):
        expires = int(getattr(settings, "B2_POSTER_PRESIGNED_EXPIRES", 604800))
        return b2_presigned_get_url(key, expires_in=expires)
    return b2_public_url(key)


def _presigned_source_url(key: str) -> str:
    s3 = get_b2_s3_client()
    cfg = get_b2_config()
    return s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": cfg.bucket_name, "Key": key.lstrip("/")},
        ExpiresIn=3600,
    )


def _probe_metadata_ffprobe(input_url: str, ffprobe: str) -> tuple[int | None, str]:
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        input_url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        return None, ""
    data = json.loads(proc.stdout or "{}")
    duration = None
    if data.get("format", {}).get("duration"):
        duration = int(float(data["format"]["duration"]))
    height = None
    streams = data.get("streams") or []
    if streams:
        height = streams[0].get("height")
    label = f"{int(height)}p" if height else ""
    return duration, label


def _probe_metadata_ffmpeg(input_url: str, ffmpeg: str) -> tuple[int | None, str]:
    """Fallback when ffprobe is not installed (ffmpeg -i parses stderr)."""
    proc = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", input_url],
        capture_output=True,
        text=True,
        timeout=120,
    )
    text = (proc.stderr or "") + (proc.stdout or "")
    duration = None
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    if m:
        h, mi, s = m.groups()
        duration = int(float(h) * 3600 + float(mi) * 60 + float(s))
    label = ""
    m2 = re.search(r"Video:.*?(\d{3,4})x(\d{3,4})", text)
    if m2:
        label = f"{int(m2.group(2))}p"
    return duration, label


def _probe_metadata(input_url: str, ffmpeg: str) -> tuple[int | None, str]:
    ffprobe = _resolve_ffprobe()
    try:
        if ffprobe:
            return _probe_metadata_ffprobe(input_url, ffprobe)
        return _probe_metadata_ffmpeg(input_url, ffmpeg)
    except Exception:
        return None, ""


def generate_poster_for_video(video) -> bool:
    """
    Extract a JPEG poster from the uploaded source, upload to B2, update video row.
    Safe to call after multipart upload completes or during HLS processing.
    """
    if not video.original_b2_key:
        return False

    ffmpeg = _resolve_ffmpeg()
    input_url = _presigned_source_url(video.original_b2_key)
    s3 = get_b2_s3_client()
    cfg = get_b2_config()

    with tempfile.TemporaryDirectory(prefix="gs_poster_") as tmpdir:
        poster_path = Path(tmpdir) / "poster.jpg"
        cmd = [
            ffmpeg,
            "-y",
            "-ss",
            "00:00:01",
            "-i",
            input_url,
            "-frames:v",
            "1",
            "-q:v",
            "3",
            "-vf",
            "scale='min(640,iw)':-2",
            str(poster_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if proc.returncode != 0 or not poster_path.is_file():
            return False

        poster_key = f"global-solutions/posters/{video.storage_path_slug}/{video.id}/poster.jpg"
        s3.upload_file(
            str(poster_path),
            cfg.bucket_name,
            poster_key,
            ExtraArgs={"ContentType": "image/jpeg"},
        )

        duration_seconds, resolution_label = _probe_metadata(input_url, ffmpeg)

        update_fields = ["poster_image_url", "updated_at"]
        video.poster_image_url = poster_url_for_key(poster_key)
        if duration_seconds and not video.duration_seconds:
            video.duration_seconds = duration_seconds
            update_fields.append("duration_seconds")
        if resolution_label and not video.resolution_label:
            video.resolution_label = resolution_label
            update_fields.append("resolution_label")
        video.save(update_fields=update_fields)
        return True
