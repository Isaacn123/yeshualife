"""Responsive image helper used across article templates."""

from __future__ import annotations

import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

_WIDTH_SPEC_RE = re.compile(r"^width-\{?([\d,\s]+)\}?$", re.I)


def _parse_widths(*args, **kwargs) -> list[int]:
    widths: list[int] = []

    for key, value in kwargs.items():
        if key.startswith("width") or key == "widths":
            for part in re.findall(r"\d+", str(value)):
                widths.append(int(part))

    for arg in args:
        raw = str(arg).strip()
        match = _WIDTH_SPEC_RE.match(raw)
        if match:
            raw = match.group(1)
        for part in re.findall(r"\d+", raw):
            widths.append(int(part))

    return sorted(set(widths), reverse=True) or [1080, 800, 640]


@register.simple_tag
def srcset_image(image, *args, **kwargs):
    """
    Render an <img> with srcset for Wagtail images.

    Usage:
      {% srcset_image page.image class="image-blog-main" width-{1080,800,640} sizes="100vw" %}
    """
    if not image:
        return ""

    class_name = kwargs.get("class", "") or ""
    sizes = kwargs.get("sizes", "100vw") or "100vw"
    alt = kwargs.get("alt", "") or getattr(image, "title", "") or ""
    widths = _parse_widths(*args, **kwargs)

    candidates = []
    for width in widths:
        try:
            rendition = image.get_rendition(f"width-{width}")
            candidates.append((rendition, width))
        except Exception:
            continue

    if not candidates:
        try:
            rendition = image.get_rendition("original")
            candidates = [(rendition, getattr(rendition, "width", 0) or 0)]
        except Exception:
            file_obj = getattr(image, "file", None)
            if not file_obj:
                return ""
            url = escape(file_obj.url)
            class_attr = f' class="{escape(class_name)}"' if class_name else ""
            return mark_safe(
                f'<img src="{url}" alt="{escape(alt)}"{class_attr} loading="lazy" decoding="async">'
            )

    primary = candidates[0][0]
    srcset = ", ".join(f"{escape(r.url)} {w}w" for r, w in candidates if w)
    class_attr = f' class="{escape(class_name)}"' if class_name else ""
    sizes_attr = f' sizes="{escape(sizes)}"' if sizes else ""
    srcset_attr = f' srcset="{srcset}"' if srcset else ""

    return mark_safe(
        f'<img src="{escape(primary.url)}"{srcset_attr}{sizes_attr}{class_attr} '
        f'alt="{escape(alt)}" loading="lazy" decoding="async">'
    )
