"""Homepage Open Graph / WhatsApp share metadata."""

from __future__ import annotations

from django.contrib.staticfiles.storage import staticfiles_storage

from blog.templatetags.social_tags import build_absolute_url

HOME_HERO_IMAGE_STATIC = "images/karamoja_re.jpg"
HOME_HERO_OG_FALLBACK = "https://yeshualifeug.com/static/images/karamoja_re.jpg"

HOME_OG_TITLE = "Karamoja's Battle Against Starvation | Yeshua Life"
HOME_OG_DESCRIPTION = (
    "Every Meal of Elijah's brings hope in the face of extreme hunger. "
    "Yeshua Life serves communities in Karamoja through agriculture, relief, "
    "and lasting solutions."
)


def _home_hero_image_path() -> str:
    try:
        if staticfiles_storage.exists(HOME_HERO_IMAGE_STATIC):
            return staticfiles_storage.url(HOME_HERO_IMAGE_STATIC)
    except Exception:
        pass
    return f"/static/{HOME_HERO_IMAGE_STATIC}"


def build_home_share_context(request, page) -> dict[str, str]:
    """Build absolute share fields for the main homepage (BlogIndexPage)."""
    seo_title = (getattr(page, "seo_title", None) or "").strip()
    page_title = (getattr(page, "title", None) or "").strip()
    title = seo_title or page_title
    if not title or title.lower() == "home":
        title = HOME_OG_TITLE

    description = (
        (getattr(page, "search_description", None) or "").strip()
        or (getattr(page, "intro", None) or "").strip()
    )
    if not description or description.lower() in {"home", title.lower()}:
        description = HOME_OG_DESCRIPTION

    image_path = _home_hero_image_path()
    image_url = build_absolute_url(request, image_path)
    if not image_url or "karamoja_re" not in image_url:
        image_url = HOME_HERO_OG_FALLBACK

    return {
        "share_url": build_absolute_url(request, "/"),
        "share_title": title,
        "share_description": description,
        "share_image_url": image_url,
        "share_type": "website",
        # Hero photo is landscape; omit wrong 1200x630 for the static JPG.
        "share_image_width": "",
        "share_image_height": "",
    }
