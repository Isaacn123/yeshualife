"""FarmHub engagement helpers — views (watch-time) and session deduplication."""

from __future__ import annotations

from django.db.models import F
from django.shortcuts import get_object_or_404

from .discovery import get_public_videos_qs
from .models import GlobalSolutionsVideo

# Industry-standard minimum watch time before counting a view (YouTube uses ~30s).
VIEW_THRESHOLD_SECONDS = 30


def session_slugs(request, session_key: str) -> set[str]:
    raw = request.session.get(session_key, [])
    if not isinstance(raw, list):
        return set()
    return {str(s) for s in raw if s}


def view_threshold_seconds(duration_seconds: int | None) -> float:
    """
    How many seconds of watch time are required to count one view.
    Short clips: ~90% of duration. Longer clips: 30 seconds (YouTube-style).
    """
    if duration_seconds and duration_seconds > 0:
        if duration_seconds < VIEW_THRESHOLD_SECONDS:
            return max(1.0, duration_seconds * 0.9)
        return float(VIEW_THRESHOLD_SECONDS)
    return float(VIEW_THRESHOLD_SECONDS)


def video_view_payload(
    video: GlobalSolutionsVideo, *, counted: bool, already_counted: bool = False
) -> dict:
    return {
        "slug": video.slug,
        "views": video.views,
        "views_display": video.views_display,
        "counted": counted,
        "already_counted": already_counted,
        "threshold_seconds": view_threshold_seconds(video.duration_seconds),
    }


def record_video_view(request, slug: str, *, watched_seconds: float) -> dict:
    """
    Count one view if watch-time threshold met and not yet counted this session.
    Returns JSON-serializable payload.
    """
    video = get_object_or_404(get_public_videos_qs(), slug=slug)
    threshold = view_threshold_seconds(video.duration_seconds)

    if watched_seconds < threshold:
        return {
            **video_view_payload(video, counted=False),
            "error": "insufficient_watch_time",
            "watched_seconds": watched_seconds,
        }

    viewed_slugs = session_slugs(request, "farmhub_viewed")
    if slug in viewed_slugs:
        return video_view_payload(video, counted=False, already_counted=True)

    GlobalSolutionsVideo.objects.filter(pk=video.pk).update(views=F("views") + 1)
    video.views += 1
    viewed_slugs.add(slug)
    request.session["farmhub_viewed"] = sorted(viewed_slugs)
    request.session.modified = True
    return video_view_payload(video, counted=True)


def video_view_counted_in_session(request, slug: str) -> bool:
    return slug in session_slugs(request, "farmhub_viewed")
