
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def canonical_url(context):
    request = context['request']
    if request.path == "/payments/":
        return "https://yeshualifeug.com/payments"
    elif request.path.startswith("/payments/"):
        return "https://yeshualifeug.com/payments"
    
    elif request.path == "/donation/":
        return "https://yeshualifeug.com/donation"
    elif request.path.startswith("/donation/"):
        return "https://yeshualifeug.com/donation"
    

    elif request.path == "/karamoja/":
        return "https://yeshualifeug.com/karamoja"
    elif request.path.startswith("/karamoja/"):
        return "https://yeshualifeug.com/karamoja"
    
    elif request.path == "/response/":
        return "https://yeshualifeug.com/response"
    elif request.path.startswith("/response/"):
        return "https://yeshualifeug.com/response"

    elif request.path == "/solution/":
        return "https://yeshualifeug.com/solution"
    elif request.path.startswith("/solution/"):
        return "https://yeshualifeug.com/solution"

    elif request.path == "/production/":
        return "https://yeshualifeug.com/production"
    elif request.path.startswith("/production/"):
        return "https://yeshualifeug.com/production"
    
    elif request.path == "/awards/":
        return "https://yeshualifeug.com/awards"
    elif request.path.startswith("/awards/"):
        return "https://yeshualifeug.com/awards"

    elif request.path == "/landclearing/":
        return "https://yeshualifeug.com/landclearing"
    elif request.path.startswith("/landclearing/"):
        return "https://yeshualifeug.com/landclearing"

    elif request.path == "/contact/":
        return "https://yeshualifeug.com/contact/"
    elif request.path.startswith("/landclearing/"):
        return "https://yeshualifeug.com/contact/"
    
    else:
        return request.build_absolute_uri()
