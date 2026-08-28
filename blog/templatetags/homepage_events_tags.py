from django import template

from blog.homepage_events import get_homepage_events_for_context

register = template.Library()


@register.simple_tag
def get_homepage_events_section():
    """Load homepage events for templates (works even without get_context wiring)."""
    return get_homepage_events_for_context()
