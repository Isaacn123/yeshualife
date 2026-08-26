"""Render blog RichText bodies and repair pasted embed HTML shown as plain text."""

from __future__ import annotations

import html as html_lib
import re

from django import template
from django.utils.safestring import mark_safe
from wagtail.embeds.embeds import get_embed
from wagtail.embeds.format import embed_to_frontend_html
from wagtail.rich_text import expand_db_html

register = template.Library()

_IFRAME_SRC_RE = re.compile(r"""<iframe[^>]+src=["']([^"']+)["']""", re.I)
_RESPONSIVE_OBJECT_RE = re.compile(
    r"(?:&lt;|<)div[^>]*class=[\"']responsive-object[\"'][^>]*(?:&gt;|>)"
    r"\s*(?:&lt;|<)iframe[^>]+(?:&gt;|>)\s*(?:&lt;|<)/iframe(?:&gt;|>)"
    r"\s*(?:&lt;|<)/div(?:&gt;|>)",
    re.I | re.S,
)
_EMBED_URL_RE = re.compile(
    r"https?://(?:www\.)?yeshualifeug\.com/(?:global-solutions|farmhub)/(?:embed|video)/[\w-]+/?",
    re.I,
)
_P_WITH_EMBED_LITERAL_RE = re.compile(
    r"<p([^>]*)>((?:.(?!</p>))*responsive-object(?:.(?!</p>))*)</p>",
    re.I | re.S,
)
_P_WITH_EMBED_URL_RE = re.compile(
    r"<p([^>]*)>\s*(https?://(?:www\.)?yeshualifeug\.com/(?:global-solutions|farmhub)/(?:embed|video)/[\w-]+/?)\s*</p>",
    re.I,
)


def _render_embed_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    try:
        embed = get_embed(url, max_width=640)
        return embed_to_frontend_html(embed)
    except Exception:
        return ""


def _replace_responsive_object(match: re.Match) -> str:
    block = html_lib.unescape(match.group(0))
    src_match = _IFRAME_SRC_RE.search(block)
    if not src_match:
        return match.group(0)
    rendered = _render_embed_url(src_match.group(1))
    return rendered or match.group(0)


def _replace_paragraph_literal(match: re.Match) -> str:
    inner = html_lib.unescape(match.group(2))
    src_match = _IFRAME_SRC_RE.search(inner)
    if src_match:
        rendered = _render_embed_url(src_match.group(1))
        if rendered:
            return rendered
    if _RESPONSIVE_OBJECT_RE.search(inner):
        return _RESPONSIVE_OBJECT_RE.sub(_replace_responsive_object, inner)
    return match.group(0)


def _replace_paragraph_url(match: re.Match) -> str:
    rendered = _render_embed_url(match.group(2))
    return rendered or match.group(0)


def repair_embed_markup(html: str) -> str:
    if not html:
        return html

    if "responsive-object" in html or _EMBED_URL_RE.search(html):
        html = _P_WITH_EMBED_URL_RE.sub(_replace_paragraph_url, html)
        html = _P_WITH_EMBED_LITERAL_RE.sub(_replace_paragraph_literal, html)
        html = _RESPONSIVE_OBJECT_RE.sub(_replace_responsive_object, html)

    return html


@register.filter
def blog_richtext(value) -> str:
    """Expand Wagtail rich text and render pasted Global Solutions embed markup."""
    if not value:
        return ""

    source = getattr(value, "source", None) or str(value)
    html = expand_db_html(source)
    html = repair_embed_markup(html)
    return mark_safe(html)
