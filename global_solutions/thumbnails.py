"""Generate video poster images and metadata via ffmpeg/ffprobe."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings

from .b2 import b2_presigned_get_url, b2_public_url, get_b2_config, get_b2_s3_client


def _ffmpeg_bin() -> str:
    return os.environ.get("FFMPEG_BIN", "ffmpeg")


def _ffprobe_bin() -> str:
    return os.environ.get("FFPROBE_BIN", "ffprobe")


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


def _probe_metadata(input_url: str) -> tuple[int | None, str]:
    """Return (duration_seconds, resolution_label e.g. 720p)."""
    cmd = [
        _ffprobe_bin(),
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
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            return None, ""
        data = json.loads(proc.stdout or "{}")
        duration = None
        if data.get("format", {}).get("duration"):
            duration = int(float(data["format"]["duration"]))
        width = height = None
        streams = data.get("streams") or []
        if streams:
            width = streams[0].get("width")
            height = streams[0].get("height")
        label = ""
        if height:
            label = f"{int(height)}p"
        elif width and height:
            label = f"{width}x{height}"
        return duration, label
    except Exception:
        return None, ""


def generate_poster_for_video(video) -> bool:
    """
    Extract a JPEG poster from the uploaded source, upload to B2, update video row.
    Safe to call after multipart upload completes or during HLS processing.
    """
    if not video.original_b2_key:
        return False

    input_url = _presigned_source_url(video.original_b2_key)
    s3 = get_b2_s3_client()
    cfg = get_b2_config()

    with tempfile.TemporaryDirectory(prefix="gs_poster_") as tmpdir:
        poster_path = Path(tmpdir) / "poster.jpg"
        cmd = [
            _ffmpeg_bin(),
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

        duration_seconds, resolution_label = _probe_metadata(input_url)

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
