from __future__ import annotations

from django import template
from django.conf import settings

register = template.Library()

_OG_FALLBACK = "/static/images/karamoja_re.jpg"


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
    if raw.startswith("//"):
        return "https:" + raw
    if raw.startswith(("http://", "https://")):
        return raw if raw.startswith("https://") else "https://" + raw[7:]
    origin = _canonical_site_origin(request)
    if raw.startswith("/"):
        return origin + raw
    return f"{origin}/{raw.lstrip('/')}"


def _image_candidate_urls(image) -> list[str]:
    """Prefer a 1200x630 JPEG rendition, then the original file URL."""
    urls: list[str] = []
    if not image:
        return urls
    for spec in ("fill-1200x630|format-jpeg", "fill-1200x630", "width-1200|format-jpeg"):
        try:
            rendition = image.get_rendition(spec)
            if rendition and getattr(rendition, "url", None):
                urls.append(rendition.url)
                break
        except Exception:
            continue
    try:
        file_url = getattr(getattr(image, "file", None), "url", None)
        if file_url:
            urls.append(file_url)
    except Exception:
        pass
    return urls


def _first_carousel_image(page):
    carousel = getattr(page, "carousel", None)
    if not carousel:
        return None
    try:
        for block in carousel:
            if getattr(block, "block_type", None) != "carousel_item":
                continue
            value = block.value
            img = None
            if hasattr(value, "get"):
                img = value.get("image")
            elif hasattr(value, "image"):
                img = value.image
            if img:
                return img
    except Exception:
        return None
    return None


def resolve_page_share_image_url(request, page) -> str:
    """
    Absolute HTTPS image URL for Open Graph / WhatsApp.

    Uses page.image, then first carousel image, then a landscape site fallback
    (not the small logo — crawlers often ignore tiny images).
    """
    specific = page
    try:
        specific = page.specific
    except Exception:
        pass

    candidates = []
    main = getattr(specific, "image", None)
    if main:
        candidates.extend(_image_candidate_urls(main))
    carousel_img = _first_carousel_image(specific)
    if carousel_img:
        candidates.extend(_image_candidate_urls(carousel_img))

    for url in candidates:
        absolute = build_absolute_url(request, url)
        if absolute:
            return absolute
    return build_absolute_url(request, _OG_FALLBACK)


@register.simple_tag(takes_context=True)
def absolute_url(context, url: str = "") -> str:
    """Build an absolute https URL for Open Graph / WhatsApp share previews."""
    return build_absolute_url(context.get("request"), url)


@register.simple_tag(takes_context=True)
def page_share_image_url(context, page=None) -> str:
    """Absolute OG image URL for the given page (defaults to context page)."""
    request = context.get("request")
    target = page or context.get("page")
    if not target:
        return build_absolute_url(request, _OG_FALLBACK)
    return resolve_page_share_image_url(request, target)


@register.simple_tag
def gs_settings():
    from global_solutions.models import GlobalSolutionsSettings

    return GlobalSolutionsSettings.load()
