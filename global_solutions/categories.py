"""Solution category helpers — single source for taxonomy lookups."""

from __future__ import annotations

from .models import SolutionCategory


def get_active_categories():
    return SolutionCategory.objects.filter(is_active=True).order_by("sort_order", "name")


def resolve_category(*, category_id: str | int | None = None, category_slug: str | None = None) -> SolutionCategory | None:
    slug = (category_slug or "").strip()
    if category_id:
        try:
            return SolutionCategory.objects.get(pk=int(category_id), is_active=True)
        except (SolutionCategory.DoesNotExist, ValueError, TypeError):
            return None
    if slug:
        try:
            return SolutionCategory.objects.get(slug=slug, is_active=True)
        except SolutionCategory.DoesNotExist:
            return None
    return None


def default_category() -> SolutionCategory | None:
    return get_active_categories().first()
