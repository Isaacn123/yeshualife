"""FarmHub discovery queries — read-only helpers for public templates and API."""

from __future__ import annotations

from django.conf import settings as django_settings
from django.db.models import Q
from django.urls import reverse

from .models import (
    Creator,
    GlobalSolutionsSettings,
    GlobalSolutionsVideo,
    GlobalSolutionsVideoStatus,
    SolutionCategory,
)


def get_public_videos_qs():
    return GlobalSolutionsVideo.objects.filter(
        is_active=True,
        status=GlobalSolutionsVideoStatus.READY,
    ).select_related("category", "creator", "creator__avatar")


def get_featured_video():
    qs = get_public_videos_qs().filter(featured=True).order_by("-published_at", "sort_order")
    featured = qs.first()
    if featured:
        return featured
    return get_public_videos_qs().order_by("-views", "-published_at").first()


def get_trending_videos(*, limit: int = 8):
    return list(
        get_public_videos_qs().order_by("-views", "-published_at", "sort_order")[:limit]
    )


def get_latest_videos(*, limit: int = 8):
    return list(get_public_videos_qs().order_by("-published_at", "sort_order")[:limit])


def get_videos_for_category(category: SolutionCategory, *, limit: int = 12):
    return list(
        get_public_videos_qs()
        .filter(category=category)
        .order_by("-published_at", "sort_order")[:limit]
    )


def get_home_categories(*, limit: int = 8):
    return list(
        SolutionCategory.objects.filter(is_active=True, show_on_home=True).order_by(
            "sort_order", "name"
        )[:limit]
    )


def get_top_creators(*, limit: int = 8):
    return list(
        Creator.objects.filter(is_active=True)
        .select_related("avatar")
        .order_by("sort_order", "name")[:limit]
    )


def search_videos(query: str, *, limit: int = 24):
    q = (query or "").strip()
    if not q:
        return []
    return list(
        get_public_videos_qs()
        .filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(tags__icontains=q)
            | Q(category__name__icontains=q)
            | Q(creator__name__icontains=q)
        )
        .distinct()
        .order_by("-views", "-published_at")[:limit]
    )


def get_related_videos(video: GlobalSolutionsVideo, *, limit: int = 8):
    qs = get_public_videos_qs().exclude(pk=video.pk)
    if video.category_id:
        qs = qs.filter(category_id=video.category_id)
    return list(qs.order_by("-views", "-published_at")[:limit])


def video_to_api_dict(video: GlobalSolutionsVideo) -> dict:
    return {
        "id": str(video.id),
        "slug": video.slug,
        "title": video.title,
        "description": video.description,
        "thumbnail_url": video.thumbnail_url,
        "playback_url": video.playback_url,
        "duration_seconds": video.duration_seconds,
        "duration_display": video.duration_display,
        "views": video.views,
        "views_display": video.views_display,
        "resolution_label": video.resolution_label,
        "featured": video.featured,
        "published_at": video.published_at.isoformat() if video.published_at else None,
        "tags": video.tags_list,
        "category": (
            {"slug": video.category.slug, "name": video.category.name}
            if video.category_id
            else None
        ),
        "creator": (
            {"slug": video.creator.slug, "name": video.creator.name}
            if video.creator_id
            else None
        ),
        "url": video.get_absolute_url(),
    }


def build_farmhub_home_context() -> dict:
    """Context for FarmHub discovery homepage."""
    settings_obj = GlobalSolutionsSettings.objects.first()
    page_title = (settings_obj.page_title if settings_obj else "FarmHub").strip() or "FarmHub"
    hero_title = (settings_obj.hero_title if settings_obj else page_title).strip() or page_title
    hero_subtitle = (settings_obj.hero_subtitle if settings_obj else "").strip()
    cap = int(getattr(django_settings, "GLOBAL_SOLUTIONS_PUBLIC_VIDEO_CAP", 72))

    categories = get_home_categories()
    category_sections = []
    for cat in categories:
        videos = get_videos_for_category(cat, limit=min(12, cap))
        if videos:
            category_sections.append({"category": cat, "videos": videos})

    return {
        "hero_title": hero_title,
        "hero_subtitle": hero_subtitle,
        "hero_image_url": (settings_obj.hero_image_url if settings_obj else "").strip(),
        "featured_video": get_featured_video(),
        "trending_videos": get_trending_videos(limit=8),
        "latest_videos": get_latest_videos(limit=8),
        "category_sections": category_sections,
        "categories": categories,
        "top_creators": get_top_creators(limit=8),
        "farmhub_search_url": reverse("global_solutions:farmhub_search"),
        "farmhub_home_url": reverse("global_solutions:farmhub_home"),
    }


def get_videos_by_category_slug(slug: str, *, limit: int = 72):
    try:
        category = SolutionCategory.objects.get(slug=slug, is_active=True)
    except SolutionCategory.DoesNotExist:
        return [], 0
    qs = get_public_videos_qs().filter(category=category)
    return list(qs.order_by("-published_at", "sort_order")[:limit]), qs.count()


def build_global_solutions_public_context() -> dict:
    """FarmHub context plus legacy keys resolved from SolutionCategory slugs (not hardcoded kind)."""
    ctx = build_farmhub_home_context()
    cap = int(getattr(django_settings, "GLOBAL_SOLUTIONS_PUBLIC_VIDEO_CAP", 72))

    feeds, feeds_total = get_videos_by_category_slug("feeding", limit=cap)
    preachings, preachings_total = get_videos_by_category_slug("preaching", limit=cap)
    learning, learning_total = get_videos_by_category_slug("learning", limit=cap)

    ctx.update(
        {
            "feeds": feeds,
            "preachings": preachings,
            "learning": learning,
            "feeds_total": feeds_total,
            "preachings_total": preachings_total,
            "learning_total": learning_total,
            "global_solutions_video_cap": cap,
            "has_any_videos": get_public_videos_qs().exists(),
        }
    )
    return ctx
