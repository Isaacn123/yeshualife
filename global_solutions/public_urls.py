"""Public and embed URL helpers (no model imports — safe during app loading)."""

from __future__ import annotations

from django.conf import settings
from django.urls import reverse


def site_base_url() -> str:
    return (getattr(settings, "WAGTAILADMIN_BASE_URL", "") or "").rstrip("/")


def absolute_url(path: str) -> str:
    path = (path or "").strip()
    if not path.startswith("/"):
        path = f"/{path}"
    base = site_base_url()
    return f"{base}{path}" if base else path


def embed_iframe_url(video) -> str:
    """Player-only embed page URL for a video row (main or similar clip)."""
    slug = (getattr(video, "slug", "") or "").strip()
    if not slug:
        return ""
    path = reverse("global_solutions:video_embed", kwargs={"slug": slug})
    return absolute_url(path)


def admin_public_video_url(video) -> str:
    """Full share page (nav, description, similar clips)."""
    slug = (getattr(video, "slug", "") or "").strip()
    if not slug:
        return ""
    return absolute_url(video.get_absolute_url())


def admin_embed_video_url(video) -> str:
    """Player-only URL for Wagtail Video embed fields and iframe previews."""
    return embed_iframe_url(video)
