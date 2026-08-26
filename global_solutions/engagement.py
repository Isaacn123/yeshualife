"""FarmHub engagement — video plays, page visits, shares, and device deduplication."""

from __future__ import annotations

from django.db.models import F
from django.http import HttpResponseBase
from django.shortcuts import get_object_or_404

from .discovery import get_public_videos_qs
from .models import GlobalSolutionsVideo, GlobalSolutionsVideoStatus

# Video play deduplication (same device, 30 days + session).
PLAYED_SESSION_KEY = "farmhub_viewed"
PLAYED_COOKIE_NAME = "fh_viewed_videos"

# Page visit deduplication for the video detail page only.
PAGE_VISITED_SESSION_KEY = "farmhub_page_visited"
PAGE_VISITED_COOKIE_NAME = "fh_page_visited_videos"

TRACKING_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days
TRACKING_COOKIE_MAX_SLUGS = 120

VIEW_THRESHOLD_SECONDS = 15
VIEW_THRESHOLD_UNKNOWN = 12


def get_engagement_video(slug: str) -> GlobalSolutionsVideo:
    """Resolve a video eligible for play/like/share/page-visit engagement."""
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


def view_threshold_seconds(duration_seconds: int | None) -> float:
    """Minimum watch time before a video play counts as a view."""
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


def _cookie_slugs(request, cookie_name: str) -> list[str]:
    raw = (request.COOKIES.get(cookie_name) or "").strip()
    if not raw:
        return []
    slugs: list[str] = []
    for part in raw.split(","):
        slug = part.strip()
        if slug and slug not in slugs:
            slugs.append(slug)
    return slugs[:TRACKING_COOKIE_MAX_SLUGS]


def _slugs_for_device(request, *, session_key: str, cookie_name: str) -> set[str]:
    return session_slugs(request, session_key) | set(_cookie_slugs(request, cookie_name))


def viewed_slugs_for_device(request) -> set[str]:
    """Videos already counted as played on this device."""
    return _slugs_for_device(
        request,
        session_key=PLAYED_SESSION_KEY,
        cookie_name=PLAYED_COOKIE_NAME,
    )


def page_visited_slugs_for_device(request) -> set[str]:
    """Video pages already counted as visited on this device."""
    return _slugs_for_device(
        request,
        session_key=PAGE_VISITED_SESSION_KEY,
        cookie_name=PAGE_VISITED_COOKIE_NAME,
    )


def _increment_session_slug(request, session_key: str, slug: str) -> None:
    slugs = session_slugs(request, session_key)
    slugs.add(slug)
    request.session[session_key] = sorted(slugs)
    request.session.modified = True


def _mark_slug_on_device(request, slug: str, *, session_key: str, cookie_name: str) -> None:
    _increment_session_slug(request, session_key, slug)
    existing = _cookie_slugs(request, cookie_name)
    if slug in existing:
        ordered = existing
    else:
        ordered = existing + [slug]
    if len(ordered) > TRACKING_COOKIE_MAX_SLUGS:
        ordered = ordered[-TRACKING_COOKIE_MAX_SLUGS:]
    pending = getattr(request, "_fh_tracking_cookies", {})
    pending[cookie_name] = ",".join(ordered)
    request._fh_tracking_cookies = pending


def apply_view_tracking_cookie(request, response: HttpResponseBase) -> HttpResponseBase:
    """Attach any pending 30-day engagement cookies (plays and/or page visits)."""
    pending = getattr(request, "_fh_tracking_cookies", {})
    for cookie_name, cookie_value in pending.items():
        response.set_cookie(
            cookie_name,
            cookie_value,
            max_age=TRACKING_COOKIE_MAX_AGE,
            httponly=True,
            samesite="Lax",
            secure=getattr(request, "is_secure", lambda: False)(),
        )
    return response


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


def video_share_payload(video: GlobalSolutionsVideo, *, counted: bool) -> dict:
    return {
        "slug": video.slug,
        "shares": video.shares,
        "shares_display": video.shares_display,
        "counted": counted,
    }


def _video_play_already_counted(request, slug: str) -> bool:
    return slug in viewed_slugs_for_device(request)


def _page_visit_already_counted(request, slug: str) -> bool:
    return slug in page_visited_slugs_for_device(request)


def record_page_visit(request, slug: str) -> GlobalSolutionsVideo:
    """
    Count one page visit when the video detail page is opened.
    Separate from video plays; deduplicated per device for 30 days.
    """
    video = get_engagement_video(slug)
    if _page_visit_already_counted(request, slug):
        return video

    GlobalSolutionsVideo.objects.filter(pk=video.pk).update(page_views=F("page_views") + 1)
    video.page_views += 1
    _mark_slug_on_device(
        request,
        slug,
        session_key=PAGE_VISITED_SESSION_KEY,
        cookie_name=PAGE_VISITED_COOKIE_NAME,
    )
    return video


def record_video_view(request, slug: str, *, watched_seconds: float) -> dict:
    """
    Count one video view after sufficient watch time (detail page or embed player).
    Same counter for the original video whether played inline or in a shared embed.
    """
    video = get_engagement_video(slug)
    threshold = view_threshold_seconds(video.duration_seconds)

    if watched_seconds < threshold:
        return {
            **video_view_payload(video, counted=False),
            "error": "insufficient_watch_time",
            "watched_seconds": watched_seconds,
        }

    if _video_play_already_counted(request, slug):
        return video_view_payload(video, counted=False, already_counted=True)

    GlobalSolutionsVideo.objects.filter(pk=video.pk).update(views=F("views") + 1)
    video.views += 1
    _mark_slug_on_device(
        request,
        slug,
        session_key=PLAYED_SESSION_KEY,
        cookie_name=PLAYED_COOKIE_NAME,
    )
    return video_view_payload(video, counted=True)


def record_video_share(request, slug: str) -> dict:
    """Increment share count each time a visitor successfully shares a video."""
    video = get_engagement_video(slug)
    GlobalSolutionsVideo.objects.filter(pk=video.pk).update(shares=F("shares") + 1)
    video.shares += 1
    return video_share_payload(video, counted=True)


def video_view_counted_in_session(request, slug: str) -> bool:
    """True when this device/session has already counted a play for the slug."""
    return _video_play_already_counted(request, slug)
