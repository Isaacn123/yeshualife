"""Wagtail embed finder for Global Solutions video page URLs."""

from __future__ import annotations

import re
from html import escape
from urllib.parse import urlparse

from django.conf import settings
from wagtail.embeds.exceptions import EmbedNotFoundException
from wagtail.embeds.finders.base import EmbedFinder

from .discovery import get_public_videos_qs
from .models import GlobalSolutionsVideo, GlobalSolutionsVideoStatus
from .public_urls import embed_iframe_url

# Public detail URLs (with optional #clip- fragment) and direct embed URLs.
_PAGE_PATH_RE = re.compile(
    r"^/(?:global-solutions|farmhub)/video/(?P<parent_slug>[\w-]+)/?$",
    re.IGNORECASE,
)
_EMBED_PATH_RE = re.compile(
    r"^/(?:global-solutions|farmhub)/embed/(?P<slug>[\w-]+)/?$",
    re.IGNORECASE,
)
_CLIP_FRAGMENT_RE = re.compile(r"^clip-(?P<clip_slug>[\w-]+)$", re.IGNORECASE)


def _site_hosts() -> set[str]:
    hosts = {"yeshualifeug.com", "www.yeshualifeug.com", "127.0.0.1", "localhost"}
    base = (getattr(settings, "WAGTAILADMIN_BASE_URL", "") or "").strip()
    if base:
        host = (urlparse(base).netloc or "").lower()
        if host:
            hosts.add(host)
            if host.startswith("www."):
                hosts.add(host[4:])
            else:
                hosts.add(f"www.{host}")
    return hosts


def parse_global_solutions_video_url(url: str) -> tuple[str | None, str | None]:
    """
    Parse a Global Solutions video URL into (video_slug, clip_slug).

    clip_slug is set when the URL uses #clip- on a parent video page.
    Returns (None, None) when the URL is not recognised.
    """
    raw = (url or "").strip()
    if not raw:
        return None, None

    parsed = urlparse(raw)
    path = parsed.path or raw
    if not path.startswith("/"):
        path = f"/{path.lstrip('/')}"

    clip_slug = None
    fragment = (parsed.fragment or "").strip()
    clip_match = _CLIP_FRAGMENT_RE.match(fragment)
    if clip_match:
        clip_slug = clip_match.group("clip_slug")

    embed_match = _EMBED_PATH_RE.match(path)
    if embed_match:
        return embed_match.group("slug"), None

    page_match = _PAGE_PATH_RE.match(path)
    if not page_match:
        return None, None

    parent_slug = page_match.group("parent_slug")
    if clip_slug:
        return parent_slug, clip_slug
    return parent_slug, None


def _url_is_on_site(url: str) -> bool:
    parsed = urlparse((url or "").strip())
    if not parsed.netloc:
        return True
    return parsed.netloc.lower() in _site_hosts()


def resolve_video_for_embed(parent_slug: str, clip_slug: str | None = None) -> GlobalSolutionsVideo | None:
    ready = GlobalSolutionsVideo.objects.filter(
        is_active=True,
        status=GlobalSolutionsVideoStatus.READY,
    ).select_related("creator", "category", "parent_video")

    if clip_slug:
        return (
            ready.filter(
                slug=clip_slug,
                parent_video__slug=parent_slug,
            ).first()
        )

    by_slug = ready.filter(slug=parent_slug).first()
    if not by_slug:
        return None
    if by_slug.parent_video_id:
        return by_slug
    if get_public_videos_qs().filter(pk=by_slug.pk).exists():
        return by_slug
    return None


class GlobalSolutionsVideoEmbedFinder(EmbedFinder):
    """Allow pasting Global Solutions video URLs into Wagtail EmbedBlock fields."""

    def accept(self, url: str) -> bool:
        if not _url_is_on_site(url):
            return False
        parent_slug, _clip_slug = parse_global_solutions_video_url(url)
        return bool(parent_slug)

    def find_embed(self, url, max_width=None, max_height=None):
        parent_slug, clip_slug = parse_global_solutions_video_url(url)
        if not parent_slug:
            raise EmbedNotFoundException

        video = resolve_video_for_embed(parent_slug, clip_slug)
        if not video:
            raise EmbedNotFoundException

        width = int(max_width) if max_width else 640
        height = int(max_height) if max_height else int(width * 9 / 16)
        iframe_src = escape(embed_iframe_url(video), quote=True)
        title = escape(video.title or "Global Solutions video", quote=True)

        html = (
            f'<iframe src="{iframe_src}" title="{title}" '
            f'width="{width}" height="{height}" frameborder="0" '
            f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
            f"allowfullscreen></iframe>"
        )

        author = ""
        if video.creator_id and video.creator:
            author = video.creator.name

        return {
            "title": video.title,
            "author_name": author,
            "provider_name": "Global Solutions",
            "type": "video",
            "thumbnail_url": video.thumbnail_url,
            "width": width,
            "height": height,
            "html": html,
        }


embed_finder_class = GlobalSolutionsVideoEmbedFinder
