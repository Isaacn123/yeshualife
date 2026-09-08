"""Helpers for homepage Response updates section."""

from __future__ import annotations

from django.utils import timezone


def get_latest_response_updates(limit: int = 3):
    """
    Latest live Response detail pages for the homepage.

    Prefers karamoja_response pages (main /response content), and also
    includes response.ResponsePage if present.
    """
    pages = []

    try:
        from karamoja_response.models import karamojaResponsePage

        pages.extend(
            list(
                karamojaResponsePage.objects.live()
                .public()
                .order_by("-first_published_at")[:limit]
            )
        )
    except Exception:
        pass

    try:
        from response.models import ResponsePage

        pages.extend(
            list(
                ResponsePage.objects.live()
                .public()
                .order_by("-first_published_at")[:limit]
            )
        )
    except Exception:
        pass

    if not pages:
        return []

    def _sort_key(page):
        return page.first_published_at or page.latest_revision_created_at or timezone.now()

    # Deduplicate by pk if both apps somehow share IDs (unlikely) — use URL path.
    seen = set()
    unique = []
    for page in sorted(pages, key=_sort_key, reverse=True):
        key = getattr(page, "url_path", None) or page.pk
        if key in seen:
            continue
        seen.add(key)
        unique.append(page)
        if len(unique) >= limit:
            break
    return unique


def get_response_carousel_page(pages):
    """First page in the list that has carousel images (for homepage slider)."""
    for page in pages or []:
        specific = getattr(page, "specific", page)
        carousel = getattr(specific, "carousel", None)
        if carousel:
            return specific
    return None


def get_response_index_url() -> str:
    try:
        from karamoja_response.models import karamojaResponseIndexPage

        index = karamojaResponseIndexPage.objects.live().public().first()
        if index:
            return index.url
    except Exception:
        pass

    try:
        from response.models import ResponseIndexPage

        index = ResponseIndexPage.objects.live().public().first()
        if index:
            return index.url
    except Exception:
        pass

    return "/response/"
