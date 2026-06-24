"""Public read-only JSON API for FarmHub video discovery."""

from __future__ import annotations

from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_protect

from .categories import get_active_categories
from .discovery import (
    get_featured_video,
    get_latest_videos,
    get_public_videos_qs,
    get_trending_videos,
    get_videos_for_category,
    search_videos,
    video_to_api_dict,
)
from .models import Creator, GlobalSolutionsVideo, SolutionCategory


def _liked_slugs(request) -> set[str]:
    raw = request.session.get("farmhub_liked", [])
    if not isinstance(raw, list):
        return set()
    return {str(s) for s in raw if s}


def _video_like_payload(video: GlobalSolutionsVideo, *, liked: bool, already_liked: bool = False) -> dict:
    return {
        "slug": video.slug,
        "likes": video.likes,
        "likes_display": video.likes_display,
        "liked": liked,
        "already_liked": already_liked,
    }


def _video_list_response(videos):
    return JsonResponse({"results": [video_to_api_dict(v) for v in videos]})


@require_GET
def api_videos_list(request):
    limit = min(int(request.GET.get("limit", 24)), 72)
    videos = list(get_public_videos_qs().order_by("-published_at")[:limit])
    return _video_list_response(videos)


@require_GET
def api_videos_trending(request):
    limit = min(int(request.GET.get("limit", 12)), 48)
    return _video_list_response(get_trending_videos(limit=limit))


@require_GET
def api_videos_latest(request):
    limit = min(int(request.GET.get("limit", 12)), 48)
    return _video_list_response(get_latest_videos(limit=limit))


@require_GET
def api_videos_featured(request):
    video = get_featured_video()
    if not video:
        return JsonResponse({"result": None})
    return JsonResponse({"result": video_to_api_dict(video)})


@require_GET
def api_videos_category(request, slug):
    try:
        category = SolutionCategory.objects.get(slug=slug, is_active=True)
    except SolutionCategory.DoesNotExist:
        return JsonResponse({"error": "Category not found"}, status=404)
    limit = min(int(request.GET.get("limit", 24)), 72)
    return _video_list_response(get_videos_for_category(category, limit=limit))


@require_GET
def api_videos_search(request):
    q = request.GET.get("q", "")
    limit = min(int(request.GET.get("limit", 24)), 72)
    return _video_list_response(search_videos(q, limit=limit))


@require_GET
def api_videos_recommended(request):
    """Simple recommendation: trending mix (same as trending for now)."""
    limit = min(int(request.GET.get("limit", 12)), 48)
    return _video_list_response(get_trending_videos(limit=limit))


@require_GET
def api_categories_list(request):
    results = [
        {
            "slug": c.slug,
            "name": c.name,
            "description": c.description,
            "show_on_home": c.show_on_home,
            "url": c.get_absolute_url(),
        }
        for c in get_active_categories()
    ]
    return JsonResponse({"results": results})


@require_GET
def api_creators_list(request):
    limit = min(int(request.GET.get("limit", 24)), 48)
    creators = Creator.objects.filter(is_active=True).order_by("sort_order", "name")[:limit]
    results = []
    for c in creators:
        avatar_url = ""
        if c.avatar_id:
            try:
                avatar_url = c.avatar.file.url
            except Exception:
                avatar_url = ""
        results.append(
            {
                "slug": c.slug,
                "name": c.name,
                "bio": c.bio,
                "avatar_url": avatar_url,
                "url": c.get_absolute_url(),
            }
        )
    return JsonResponse({"results": results})


@csrf_protect
@require_POST
def api_video_like(request, slug):
    """Increment like count once per browser session per video."""
    video = get_object_or_404(get_public_videos_qs(), slug=slug)
    liked_slugs = _liked_slugs(request)
    if slug in liked_slugs:
        return JsonResponse(_video_like_payload(video, liked=True, already_liked=True))

    GlobalSolutionsVideo.objects.filter(pk=video.pk).update(likes=F("likes") + 1)
    video.likes += 1
    liked_slugs.add(slug)
    request.session["farmhub_liked"] = sorted(liked_slugs)
    request.session.modified = True
    return JsonResponse(_video_like_payload(video, liked=True))
