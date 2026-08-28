from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.homepage_events import HomepageEvent, HomepageEventsSettings, get_homepage_events_for_context
from blog.models import BlogIndexPage
from wagtail.models import Site


class Command(BaseCommand):
    help = "Print why homepage events may or may not appear on the site."

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write(f"Server time: {now.isoformat()}\n")

        site = Site.objects.filter(is_default_site=True).first()
        if site:
            root = site.root_page.specific
            self.stdout.write(f"Site root page: {root.title} ({root.__class__.__name__}) url={root.url}")
        else:
            self.stdout.write(self.style.WARNING("No default Wagtail site found."))

        blog_home = BlogIndexPage.objects.live().first()
        if blog_home:
            self.stdout.write(f"BlogIndexPage: {blog_home.title} url={blog_home.url} (events wired here)")
        else:
            self.stdout.write(self.style.WARNING("No live BlogIndexPage found."))

        self.stdout.write("\n--- Homepage events settings ---")
        settings_rows = HomepageEventsSettings.objects.all()
        if not settings_rows:
            self.stdout.write(self.style.WARNING("No settings row — create one in Snippets → Homepage events settings."))
        for row in settings_rows:
            self.stdout.write(
                f"  pk={row.pk} section_enabled={row.section_enabled} max_items={row.max_items}"
            )

        self.stdout.write("\n--- Homepage events ---")
        events = HomepageEvent.objects.all()
        if not events:
            self.stdout.write(self.style.WARNING("No events — add one in Snippets → Homepage events & announcements."))
        for event in events:
            visible = event.is_visible_now
            style = self.style.SUCCESS if visible else self.style.ERROR
            self.stdout.write(style(
                f"  pk={event.pk} active={event.is_active} visible_now={visible} "
                f"title={event.title!r} starts={event.starts_at} ends={event.ends_at}"
            ))

        ctx = get_homepage_events_for_context()
        self.stdout.write("\n--- Result ---")
        if ctx and ctx.get("events"):
            self.stdout.write(self.style.SUCCESS(
                f"Section WOULD show with {len(ctx['events'])} card(s)."
            ))
        else:
            self.stdout.write(self.style.ERROR("Section would NOT show on the homepage."))
            settings = HomepageEventsSettings.load()
            if not settings.section_enabled:
                self.stdout.write("  → Turn on Section enabled in Homepage events settings.")
            if not HomepageEvent.get_visible(limit=12):
                self.stdout.write("  → No visible events (check Is active, Starts at, Ends at).")
