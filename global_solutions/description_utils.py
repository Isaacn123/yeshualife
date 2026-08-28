"""Helpers for splitting video descriptions on detail pages."""

from __future__ import annotations

import re

from django.utils.html import strip_tags
from wagtail.rich_text import expand_db_html

DEFAULT_SIDEBAR_WORD_LIMIT = 60

_RICHTEXT_MEDIA_RE = re.compile(
    r"<embed\s+embedtype=[\"'](?:image|media)[\"']",
    re.I,
)
_RICHTEXT_HTML_MEDIA_RE = re.compile(
    r"<(?:img|iframe|video|figure)\b|responsive-object",
    re.I,
)


def _description_source(value) -> str:
    return getattr(value, "source", None) or str(value or "")


def has_richtext_media(value) -> bool:
    """True when the description contains uploaded images or embedded media."""
    raw = _description_source(value)
    if _RICHTEXT_MEDIA_RE.search(raw):
        return True
    html = expand_db_html(raw)
    return bool(_RICHTEXT_HTML_MEDIA_RE.search(html))


def split_description_text(text: str, word_limit: int = DEFAULT_SIDEBAR_WORD_LIMIT) -> tuple[str, str]:
    """
    Return (sidebar_lead, remainder) for plain-text descriptions.

    Strips HTML first so tags do not affect word counts or display.
    """
    plain = strip_tags(text or "").strip()
    if not plain:
        return "", ""

    word_end = 0
    count = 0
    for match in re.finditer(r"\S+", plain):
        count += 1
        if count == word_limit:
            word_end = match.end()
            break

    if word_end == 0:
        return plain, ""

    return plain[:word_end].rstrip(), plain[word_end:].lstrip()


def split_description_for_detail(
    value,
    word_limit: int = DEFAULT_SIDEBAR_WORD_LIMIT,
) -> tuple[str, str, bool]:
    """
    Return (sidebar_lead, body_remainder, use_full_richtext).

    Plain descriptions keep the existing sidebar/body split. When images or
    embeds are present, the full rich text is rendered in the body so media
    is never dropped from a plain-text remainder.
    """
    raw = _description_source(value)
    plain = strip_tags(expand_db_html(raw)).strip()
    if not plain:
        return "", "", False

    lead, rest = split_description_text(plain, word_limit)
    if has_richtext_media(value):
        return lead, "", True
    return lead, rest, False
