
from django.utils.safestring import mark_safe
from django import template

register = template.Library()
from wagtail.rich_text import expand_db_html

@register.filter 
def betterhtml(html):
    return mark_safe(expand_db_html(html))