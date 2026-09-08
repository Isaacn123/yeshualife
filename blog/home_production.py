"""Helpers for homepage Machinery & Production section."""

from __future__ import annotations

from django.utils import timezone


def get_latest_production_pages(limit: int = 10):
    """Latest live Production detail pages."""
    try:
        from production.models import ProductionPage

        pages = list(
            ProductionPage.objects.live()
            .public()
            .order_by("-first_published_at")[:limit]
        )
    except Exception:
        return []

    def _sort_key(page):
        return page.first_published_at or page.latest_revision_created_at or timezone.now()

    return sorted(pages, key=_sort_key, reverse=True)


def get_production_carousel_page(pages=None):
    """
    First Production page with carousel images (same StreamField as detail pages).
    Searches provided pages, then a wider live set if needed.
    """
    candidates = list(pages or [])
    if not candidates:
        candidates = get_latest_production_pages(limit=20)

    for page in candidates:
        specific = getattr(page, "specific", page)
        carousel = getattr(specific, "carousel", None)
        if carousel:
            return specific
    return None


def get_production_index_url() -> str:
    try:
        from production.models import ProductionIndexPage

        index = ProductionIndexPage.objects.live().public().first()
        if index:
            return index.url
    except Exception:
        pass

    return "/production/"
