"""FarmHub engagement helpers — views (watch-time) and session deduplication."""

from __future__ import annotations

from django.db.models import F
from django.shortcuts import get_object_or_404

from .discovery import get_public_videos_qs
from .models import GlobalSolutionsVideo, GlobalSolutionsVideoStatus


def get_engagement_video(slug: str) -> GlobalSolutionsVideo:
    """
    Resolve a video eligible for view/like engagement.
    Includes public hub videos and embedded similar clips (child rows).
    """
    video = get_object_or_404(
        GlobalSolutionsVideo.objects.filter(
            is_active=True,
            status=GlobalSolutionsVideoStatus.READY,
        ),
        slug=slug,
    )
    if video.parent_video_id:
        return video
    get_object_or_404(get_public_videos_qs(), slug=slug)
    return video

# Minimum watch time before counting a view (seconds).
VIEW_THRESHOLD_SECONDS = 15
VIEW_THRESHOLD_UNKNOWN = 12


def view_threshold_seconds(duration_seconds: int | None) -> float:
    """
    How many seconds of watch time are required to count one view.
    Short clips: 50% of duration. Medium: 50% up to 8s min. Long: 15 seconds.
    """
    if duration_seconds and duration_seconds > 0:
        if duration_seconds <= 15:
            return max(3.0, duration_seconds * 0.5)
        if duration_seconds < 60:
            return max(8.0, duration_seconds * 0.5)
        return float(VIEW_THRESHOLD_SECONDS)
    return float(VIEW_THRESHOLD_UNKNOWN)


def session_slugs(request, session_key: str) -> set[str]:
    raw = request.session.get(session_key, [])
    if not isinstance(raw, list):
        return set()
    return {str(s) for s in raw if s}


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
    video = get_engagement_video(slug)
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
