from django.http import Http404
from django.shortcuts import get_object_or_404, render

from blog.homepage_events import HomepageEvent, HomepageEventsSettings


def homepage_event_detail(request, slug):
    event = get_object_or_404(HomepageEvent, slug=slug)
    if not event.is_active:
        raise Http404("Event not available.")
    return render(
        request,
        "blog/homepage_event_detail.html",
        {
            "event": event,
            "event_settings": HomepageEventsSettings.load(),
        },
    )
