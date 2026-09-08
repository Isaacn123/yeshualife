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


def get_production_carousel_slides(max_slides: int = 24):
    """
    Collect carousel images from every live Production page that has them.

    Returns a list of dicts: {"image": Image, "page": ProductionPage}
    Newest pages first; slides within a page keep their StreamField order.
    """
    try:
        from production.models import ProductionPage

        pages = list(
            ProductionPage.objects.live().public().order_by("-first_published_at")
        )
    except Exception:
        return []

    slides = []
    for page in pages:
        specific = getattr(page, "specific", page)
        carousel = getattr(specific, "carousel", None)
        if not carousel:
            continue
        for block in carousel:
            if getattr(block, "block_type", None) != "carousel_item":
                continue
            img = None
            try:
                img = block.value.get("image") if hasattr(block.value, "get") else block.value["image"]
            except Exception:
                img = getattr(block.value, "image", None)
            if not img:
                continue
            slides.append({"image": img, "page": specific})
            if len(slides) >= max_slides:
                return slides
    return slides


def get_production_index_url() -> str:
    try:
        from production.models import ProductionIndexPage

        index = ProductionIndexPage.objects.live().public().first()
        if index:
            return index.url
    except Exception:
        pass

    return "/production/"
