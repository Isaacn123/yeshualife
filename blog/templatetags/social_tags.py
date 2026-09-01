from __future__ import annotations

from django import template
from django.conf import settings

register = template.Library()


def _canonical_site_origin(request=None) -> str:
    """HTTPS site origin for Open Graph / WhatsApp crawlers."""
    configured = (getattr(settings, "WAGTAILADMIN_BASE_URL", "") or "").strip().rstrip("/")
    if configured:
        origin = configured
    elif request:
        origin = request.build_absolute_uri("/").rstrip("/")
    else:
        origin = "https://yeshualifeug.com"
    if origin.startswith("http://"):
        origin = "https://" + origin[7:]
    return origin


def build_absolute_url(request, url: str = "") -> str:
    """Build an absolute https URL for share previews."""
    raw = (url or "").strip()
    if not raw:
        return _canonical_site_origin(request)
    if raw.startswith(("http://", "https://")):
        return raw if raw.startswith("https://") else "https://" + raw[7:]
    origin = _canonical_site_origin(request)
    if raw.startswith("/"):
        return origin + raw
    return f"{origin}/{raw.lstrip('/')}"


@register.simple_tag(takes_context=True)
def absolute_url(context, url: str = "") -> str:
    """Build an absolute https URL for Open Graph / WhatsApp share previews."""
    return build_absolute_url(context.get("request"), url)


@register.simple_tag
def gs_settings():
    from global_solutions.models import GlobalSolutionsSettings

    return GlobalSolutionsSettings.load()
