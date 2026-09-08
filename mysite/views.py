from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET


def robots_txt(request):
    """Serve crawl rules for search engines (overrides the old Disallow: / file)."""
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /django-admin/",
        "Disallow: /api/",
        "Disallow: /api_auth/",
        "",
        "Sitemap: https://yeshualifeug.com/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


@require_GET
@cache_control(public=True, max_age=86400)
def og_share_image(request, image_id: int):
    """
    Same-origin Open Graph image for WhatsApp / Facebook.

    Crawlers often fail to fetch images hosted on *.r2.dev. Serving a 1200x630
    JPEG from yeshualifeug.com fixes missing share thumbnails.
    """
    from wagtail.images.models import Image

    image = get_object_or_404(Image, pk=image_id)
    rendition = None
    for spec in ("fill-1200x630|format-jpeg", "fill-1200x630", "width-1200"):
        try:
            rendition = image.get_rendition(spec)
            break
        except Exception:
            continue
    if rendition is None:
        raise Http404("Image rendition unavailable")

    try:
        file_handle = rendition.file.open("rb")
    except Exception as exc:
        raise Http404("Image file unavailable") from exc

    content_type = "image/jpeg"
    name = (getattr(rendition.file, "name", "") or "").lower()
    if name.endswith(".png"):
        content_type = "image/png"
    elif name.endswith(".webp"):
        content_type = "image/webp"

    response = FileResponse(file_handle, content_type=content_type)
    response["Content-Disposition"] = "inline"
    return response
