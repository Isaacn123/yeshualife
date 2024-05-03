from django import template
import re

register = template.Library()

@register.filter
def striphtml(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)
