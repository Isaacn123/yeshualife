from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from blog.homepage_events import HomepageEvent, HomepageEventsSettings
from blog.templatetags.social_tags import build_absolute_url


def homepage_event_detail(request, slug):
    event = get_object_or_404(HomepageEvent, slug=slug)
    if not event.is_active:
        raise Http404("Event not available.")
    share_url = build_absolute_url(request, event.get_absolute_url())
    share_image_url = event.og_image_path or staticfiles_storage.url("images/yeshua_logo2.png")
    return render(
        request,
        "blog/homepage_event_detail.html",
        {
            "event": event,
            "event_settings": HomepageEventsSettings.load(),
            "share_url": share_url,
            "share_image_url": share_image_url,
        },
    )
