# myapp/templatetags/htmlmin.py
from django import template
from htmlmin import minify

register = template.Library()

@register.filter
def minify_html(value):
    return minify(value)
