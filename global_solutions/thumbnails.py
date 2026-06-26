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


class ThumbnailGenerationError(RuntimeError):
    def __init__(self, message: str, *, detail: str = "", ffmpeg_path: str = ""):
        super().__init__(message)
        self.detail = detail
        self.ffmpeg_path = ffmpeg_path


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
        "ffmpeg not found. Install imageio-ffmpeg in the same venv gunicorn uses, "
        "or apt install ffmpeg, or set FFMPEG_BIN=/full/path/to/ffmpeg"
    )


def _resolve_ffprobe() -> str | None:
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
    return _resolve_ffmpeg()


def ffmpeg_diagnostic() -> dict:
    configured = (os.environ.get("FFMPEG_BIN") or getattr(settings, "FFMPEG_BIN", "") or "").strip()
    bundled = _bundled_ffmpeg()
    which = shutil.which("ffmpeg")
    try:
        resolved = _resolve_ffmpeg()
        version_proc = subprocess.run(
            [resolved, "-version"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        lines = (version_proc.stdout or version_proc.stderr or "").splitlines()
        version = lines[0] if lines else "unknown"
    except Exception as exc:
        resolved = ""
        version = f"unavailable: {exc}"
    return {
        "configured": configured or None,
        "bundled_imageio": bundled,
        "path_which": which,
        "resolved": resolved or None,
        "version": version,
    }


def poster_url_for_key(key: str) -> str:
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
    return bool(re.fullmatch(r"candidate-[1-9]\d*\.jpg", name))


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


def _probe_metadata_ffmpeg(input_source: str, ffmpeg: str) -> tuple[int | None, str]:
    proc = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", input_source],
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


def _probe_metadata(input_source: str, ffmpeg: str) -> tuple[int | None, str]:
    ffprobe = _resolve_ffprobe()
    try:
        if ffprobe:
            return _probe_metadata_ffprobe(input_source, ffprobe)
        return _probe_metadata_ffmpeg(input_source, ffmpeg)
    except Exception:
        return None, ""


def _frame_timestamps(duration_seconds: int | None, count: int = CANDIDATE_COUNT) -> list[float]:
    if duration_seconds and duration_seconds > 6:
        ratios = (0.08, 0.45, 0.82)
        return [max(0.5, min(duration_seconds - 0.5, duration_seconds * r)) for r in ratios[:count]]
    return [1.0, 3.0, 6.0][:count]


def _extract_frame(ffmpeg: str, input_source: str, seconds: float, output_path: Path) -> tuple[bool, str]:
    seconds = max(0.0, float(seconds))
    cmd = [
        ffmpeg,
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{seconds:.3f}",
        "-i",
        input_source,
        "-frames:v",
        "1",
        "-q:v",
        "3",
        "-vf",
        "scale=1280:-2",
        "-y",
        str(output_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode == 0 and output_path.is_file() and output_path.stat().st_size > 0:
        return True, ""
    detail = (proc.stderr or proc.stdout or "ffmpeg produced no output").strip()
    return False, detail[:500]


def _download_source_video(s3, cfg, key: str, dest: Path) -> None:
    s3.download_file(cfg.bucket_name, key.lstrip("/"), str(dest))


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
    candidates = []
    for n in range(1, CANDIDATE_COUNT + 1):
        key = candidate_b2_key(video, n)
        if _b2_object_exists(key):
            candidates.append(candidate_dict(video, n))

    custom = None
    custom_key = custom_poster_b2_key(video)
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


def _upload_generated_frames(
    video,
    s3,
    cfg,
    frames: list[tuple[int, float, Path]],
) -> list[dict]:
    generated: list[dict] = []
    for index, seconds, poster_path in frames:
        key = candidate_b2_key(video, index)
        s3.upload_file(
            str(poster_path),
            cfg.bucket_name,
            key,
            ExtraArgs={"ContentType": "image/jpeg"},
        )
        generated.append(candidate_dict(video, index, seconds=seconds))
    return generated


def generate_poster_candidates(video, *, count: int = CANDIDATE_COUNT) -> list[dict]:
    if not video.original_b2_key:
        return []

    try:
        ffmpeg = _resolve_ffmpeg()
    except FFmpegNotFoundError as exc:
        raise ThumbnailGenerationError(str(exc), ffmpeg_path="") from exc

    s3 = get_b2_s3_client()
    cfg = get_b2_config()
    input_url = _presigned_source_url(video.original_b2_key)
    duration_seconds, resolution_label = _probe_metadata(input_url, ffmpeg)
    timestamps = _frame_timestamps(duration_seconds, count=count)
    errors: list[str] = []
    generated: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="gs_poster_") as tmpdir:
        tmp = Path(tmpdir)
        ok_frames: list[tuple[int, float, Path]] = []

        for index, seconds in enumerate(timestamps, start=1):
            poster_path = tmp / f"candidate-{index}.jpg"
            ok, err = _extract_frame(ffmpeg, input_url, seconds, poster_path)
            if ok:
                ok_frames.append((index, seconds, poster_path))
            elif err:
                errors.append(f"option {index} @ {seconds:.1f}s (url): {err}")

        if not ok_frames:
            local_source = tmp / "source.mp4"
            try:
                _download_source_video(s3, cfg, video.original_b2_key, local_source)
            except Exception as exc:
                raise ThumbnailGenerationError(
                    "Could not read video from B2 for thumbnail generation.",
                    detail=f"download failed: {exc}; ffmpeg errors: {' | '.join(errors)}",
                    ffmpeg_path=ffmpeg,
                ) from exc

            if not local_source.is_file() or local_source.stat().st_size == 0:
                raise ThumbnailGenerationError(
                    "Downloaded video file is empty.",
                    detail=" | ".join(errors),
                    ffmpeg_path=ffmpeg,
                )

            if not duration_seconds:
                duration_seconds, resolution_label = _probe_metadata(str(local_source), ffmpeg)
                timestamps = _frame_timestamps(duration_seconds, count=count)

            ok_frames = []
            errors = []
            for index, seconds in enumerate(timestamps, start=1):
                poster_path = tmp / f"candidate-{index}.jpg"
                ok, err = _extract_frame(ffmpeg, str(local_source), seconds, poster_path)
                if ok:
                    ok_frames.append((index, seconds, poster_path))
                elif err:
                    errors.append(f"option {index} @ {seconds:.1f}s (local): {err}")

        if ok_frames:
            generated = _upload_generated_frames(video, s3, cfg, ok_frames)

    if not generated:
        diag = ffmpeg_diagnostic()
        raise ThumbnailGenerationError(
            "Could not extract any thumbnail frames from the video.",
            detail=" | ".join(errors) or "ffmpeg returned no frames",
            ffmpeg_path=ffmpeg,
        )

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
    try:
        return bool(generate_poster_candidates(video))
    except ThumbnailGenerationError:
        return False
