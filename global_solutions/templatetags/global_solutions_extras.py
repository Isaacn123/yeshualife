from django import template

register = template.Library()

_TITLE_SCALE_SUFFIXES = (
    (85, "--xl"),
    (60, "--long"),
    (42, "--medium"),
)


def _title_scale_suffix(title: str) -> str:
    text = (title or "").strip()
    if not text:
        return ""
    word_count = len(text.split())
    length = len(text)
    # Keep short titles (e.g. "Afri Aid Program") on the default styling.
    if word_count <= 4 and length < 42:
        return ""
    for threshold, suffix in _TITLE_SCALE_SUFFIXES:
        if length >= threshold:
            return suffix
    return ""


@register.filter
def title_scale_class(title, base_class: str = "fh-video-title") -> str:
    """Add a length-based modifier class for responsive video titles."""
    suffix = _title_scale_suffix(title)
    if suffix:
        return f"{base_class} {base_class}{suffix}"
    return base_class
