from __future__ import annotations

from django import template
from django.conf import settings

register = template.Library()


def _site_origin(request) -> str:
    if request:
        return request.build_absolute_uri("/").rstrip("/")
    base = getattr(settings, "WAGTAILADMIN_BASE_URL", "") or "https://yeshualifeug.com"
    return base.rstrip("/")


@register.simple_tag(takes_context=True)
def absolute_url(context, url: str = "") -> str:
    """Build an absolute https URL for Open Graph / WhatsApp share previews."""
    raw = (url or "").strip()
    if not raw:
        return _site_origin(context.get("request"))
    if raw.startswith(("http://", "https://")):
        return raw
    origin = _site_origin(context.get("request"))
    if raw.startswith("/"):
        return origin + raw
    return f"{origin}/{raw.lstrip('/')}"


@register.simple_tag
def gs_settings():
    from global_solutions.models import GlobalSolutionsSettings

    return GlobalSolutionsSettings.load()
