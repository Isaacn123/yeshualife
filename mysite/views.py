from django.http import HttpResponse


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
