from django import template

from blog.homepage_events import get_homepage_events_for_context

register = template.Library()


@register.simple_tag
def get_homepage_events_section(mode="auto"):
    """
    mode: auto | section | popup
    - section: full-width block (2+ events only)
    - popup: bottom-right card (single event only)
    """
    data = get_homepage_events_for_context()
    if not data or not data.get("events"):
        return None
    count = len(data["events"])
    if mode == "section" and count == 1:
        return None
    if mode == "popup" and count != 1:
        return None
    return data
