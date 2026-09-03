"""Responsive image helper used across article templates."""

from __future__ import annotations

import re

from django import template
from django.core.files.storage import default_storage
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


def _storage_has_file(file_field) -> bool:
    if not file_field:
        return False
    name = getattr(file_field, "name", "") or ""
    if not name:
        return False
    try:
        storage = getattr(file_field, "storage", None) or default_storage
        return bool(storage.exists(name))
    except Exception:
        # If storage check fails, keep the rendition and let the browser decide.
        return True


def _get_rendition(image, spec: str):
    """
    Return a Wagtail rendition whose file actually exists in storage.

    After migrating to R2, old Rendition rows can still point at local-style
    keys like images/foo.width-1080.jpg while the real object is
    images/foo.<hash>.width-1080.jpg (or another filter). Delete the stale
    row and regenerate so the URL matches R2.
    """
    try:
        rendition = image.get_rendition(spec)
    except Exception:
        return None

    if _storage_has_file(getattr(rendition, "file", None)):
        return rendition

    try:
        rendition.delete()
    except Exception:
        return None

    try:
        return image.get_rendition(spec)
    except Exception:
        return None


@register.simple_tag
def srcset_image(image, *args, **kwargs):
    """
    Render an <img> with srcset for Wagtail images.

    Usage:
      {% srcset_image page.image class="image-blog-main" widths="1080,800,640" sizes="100vw" %}
    """
    if not image:
        return ""

    class_name = kwargs.get("class", "") or ""
    sizes = kwargs.get("sizes", "100vw") or "100vw"
    alt = kwargs.get("alt", "") or getattr(image, "title", "") or ""
    widths = _parse_widths(*args, **kwargs)

    candidates = []
    for width in widths:
        rendition = _get_rendition(image, f"width-{width}")
        if rendition:
            candidates.append((rendition, width))

    if not candidates:
        # Prefer an existing working fill rendition, then original upload.
        for spec, width in (
            ("fill-1080x608", 1080),
            ("fill-800x450", 800),
            ("fill-640x400", 640),
            ("original", 0),
        ):
            rendition = _get_rendition(image, spec) if spec != "original" else None
            if spec == "original":
                try:
                    rendition = image.get_rendition("original")
                except Exception:
                    rendition = None
            if rendition and _storage_has_file(getattr(rendition, "file", None)):
                w = width or getattr(rendition, "width", 0) or 0
                candidates.append((rendition, w))
                break

    if not candidates:
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
