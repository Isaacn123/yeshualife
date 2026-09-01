from django import template

from blog.templatetags.social_tags import build_absolute_url

register = template.Library()


@register.simple_tag(takes_context=True)
def canonical_url(context):
    """
    Canonical URL for the current page.

    Each page should point to itself so Google can index articles and sub-pages.
    Only merge true duplicates (e.g. multiple payment URLs).
    """
    request = context["request"]
    path = request.path
    if path == "/payments" or path.startswith("/payments/"):
        return build_absolute_url(request, "/payments/")
    return build_absolute_url(request, path)
