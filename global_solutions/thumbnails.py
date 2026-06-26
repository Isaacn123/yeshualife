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

from .b2 import b2_head_object, b2_presigned_get_url, b2_public_url, get_b2_config, get_b2_s3_client


class FFmpegNotFoundError(FileNotFoundError):
    """Raised when ffmpeg cannot be located."""


CANDIDATE_COUNT = 3


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


def poster_dir_for_video(video) -> str:
    return f"global-solutions/posters/{video.storage_path_slug}/{video.id}"


def candidate_b2_key(video, index: int) -> str:
    return f"{poster_dir_for_video(video)}/candidate-{index}.jpg"


def custom_poster_b2_key(video) -> str:
    return f"{poster_dir_for_video(video)}/custom.jpg"


def canonical_poster_b2_key(video) -> str:
    return f"{poster_dir_for_video(video)}/poster.jpg"


def poster_key_allowed_for_video(video, key: str) -> bool:
    prefix = poster_dir_for_video(video) + "/"
    key = (key or "").strip().lstrip("/")
    if not key.startswith(prefix):
        return False
    name = key[len(prefix) :]
    if name in {"poster.jpg", "custom.jpg"}:
        return True
    if re.fullmatch(r"candidate-[1-9]\d*\.jpg", name):
        return True
    return False


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


def _frame_timestamps(duration_seconds: int | None, count: int = CANDIDATE_COUNT) -> list[float]:
    if duration_seconds and duration_seconds > 6:
        ratios = (0.08, 0.45, 0.82)
        return [max(0.5, min(duration_seconds - 0.5, duration_seconds * r)) for r in ratios[:count]]
    return [1.0, 4.0, 9.0][:count]


def _format_timestamp(seconds: float) -> str:
    whole = int(seconds)
    frac = seconds - whole
    h, rem = divmod(whole, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}.{int(frac * 100):02d}"
    return f"{m:02d}:{s:02d}.{int(frac * 100):02d}"


def _extract_frame(ffmpeg: str, input_url: str, seconds: float, output_path: Path) -> bool:
    cmd = [
        ffmpeg,
        "-y",
        "-ss",
        _format_timestamp(seconds),
        "-i",
        input_url,
        "-frames:v",
        "1",
        "-q:v",
        "3",
        "-vf",
        "scale='min(1280,iw)':-2",
        str(output_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return proc.returncode == 0 and output_path.is_file()


def _b2_object_exists(key: str) -> bool:
    try:
        b2_head_object(key)
        return True
    except Exception:
        return False


def candidate_dict(video, index: int, *, seconds: float | None = None) -> dict:
    key = candidate_b2_key(video, index)
    item = {
        "id": str(index),
        "b2_key": key,
        "url": poster_url_for_key(key),
        "label": f"Option {index}",
    }
    if seconds is not None:
        item["seconds"] = round(seconds, 2)
    return item


def list_thumbnail_options(video) -> dict:
    """Return current poster + any generated candidates already on B2."""
    candidates = []
    for n in range(1, CANDIDATE_COUNT + 1):
        key = candidate_b2_key(video, n)
        if _b2_object_exists(key):
            candidates.append(candidate_dict(video, n))

    custom_key = custom_poster_b2_key(video)
    custom = None
    if _b2_object_exists(custom_key):
        custom = {
            "id": "custom",
            "b2_key": custom_key,
            "url": poster_url_for_key(custom_key),
            "label": "Custom upload",
        }

    return {
        "poster_url": (video.poster_image_url or "").strip(),
        "candidates": candidates,
        "custom": custom,
    }


def generate_poster_candidates(video, *, count: int = CANDIDATE_COUNT) -> list[dict]:
    """
    Extract ``count`` JPEG frames from the source video, upload to B2, set default poster.
    Returns candidate metadata for the staff thumbnail picker.
    """
    if not video.original_b2_key:
        return []

    ffmpeg = _resolve_ffmpeg()
    input_url = _presigned_source_url(video.original_b2_key)
    s3 = get_b2_s3_client()
    cfg = get_b2_config()

    duration_seconds, resolution_label = _probe_metadata(input_url, ffmpeg)
    timestamps = _frame_timestamps(duration_seconds, count=count)
    generated: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="gs_poster_") as tmpdir:
        for index, seconds in enumerate(timestamps, start=1):
            poster_path = Path(tmpdir) / f"candidate-{index}.jpg"
            if not _extract_frame(ffmpeg, input_url, seconds, poster_path):
                continue

            key = candidate_b2_key(video, index)
            s3.upload_file(
                str(poster_path),
                cfg.bucket_name,
                key,
                ExtraArgs={"ContentType": "image/jpeg"},
            )
            generated.append(candidate_dict(video, index, seconds=seconds))

    if generated:
        select_video_poster(video, generated[0]["b2_key"], save=False)

    update_fields = ["poster_image_url", "updated_at"]
    if duration_seconds and not video.duration_seconds:
        video.duration_seconds = duration_seconds
        update_fields.append("duration_seconds")
    if resolution_label and not video.resolution_label:
        video.resolution_label = resolution_label
        update_fields.append("resolution_label")
    video.save(update_fields=update_fields)
    return generated


def select_video_poster(video, b2_key: str, *, save: bool = True) -> str:
    key = (b2_key or "").strip().lstrip("/")
    if not poster_key_allowed_for_video(video, key):
        raise ValueError("Invalid poster key for this video.")
    video.poster_image_url = poster_url_for_key(key)
    if save:
        video.save(update_fields=["poster_image_url", "updated_at"])
    return video.poster_image_url


def upload_custom_poster(video, uploaded_file) -> dict:
    if not video.original_b2_key:
        raise ValueError("Video has no source file.")

    content_type = (getattr(uploaded_file, "content_type", "") or "").lower()
    allowed = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
    if content_type and content_type not in allowed:
        raise ValueError("Upload a JPEG, PNG, or WebP image.")

    max_bytes = int(getattr(settings, "GLOBAL_SOLUTIONS_POSTER_MAX_BYTES", 5 * 1024 * 1024))
    if uploaded_file.size > max_bytes:
        raise ValueError("Image is too large (max 5 MB).")

    s3 = get_b2_s3_client()
    cfg = get_b2_config()
    key = custom_poster_b2_key(video)

    ext = Path(getattr(uploaded_file, "name", "") or "custom.jpg").suffix.lower()
    upload_content_type = "image/jpeg"
    if ext == ".png":
        upload_content_type = "image/png"
    elif ext == ".webp":
        upload_content_type = "image/webp"

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext or ".jpg") as tmp:
        for chunk in uploaded_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        s3.upload_file(
            tmp_path,
            cfg.bucket_name,
            key,
            ExtraArgs={"ContentType": upload_content_type},
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    url = select_video_poster(video, key)
    return {
        "id": "custom",
        "b2_key": key,
        "url": url,
        "label": "Custom upload",
    }


def generate_poster_for_video(video) -> bool:
    """Back-compat: generate candidates and use the first as the poster."""
    return bool(generate_poster_candidates(video))
