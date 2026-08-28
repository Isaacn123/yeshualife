from __future__ import annotations

from django.db import models
from django.utils import timezone
from django.utils.formats import date_format

from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet


def _wagtail_image_rendition_url(image, *, spec: str = "fill-640x360") -> str:
    if not image:
        return ""
    try:
        return image.get_rendition(spec).url
    except Exception:
        file_obj = getattr(image, "file", None)
        return file_obj.url if file_obj else ""


class HomepageEventKind(models.TextChoices):
    EVENT = "event", "Event"
    ANNOUNCEMENT = "announcement", "Announcement"
    PROMO = "promo", "Promo"


@register_snippet
class HomepageEventsSettings(models.Model):
    """Singleton settings for the homepage events & announcements section."""

    section_enabled = models.BooleanField(
        default=False,
        help_text="Show the events section on the main homepage.",
    )
    section_eyebrow = models.CharField(
        max_length=80,
        blank=True,
        default="What's next",
    )
    section_title = models.CharField(
        max_length=160,
        default="Upcoming events & announcements",
    )
    section_lead = models.TextField(
        blank=True,
        default="Join us in the field, online, and in community — dates and highlights worth marking on your calendar.",
    )
    max_items = models.PositiveSmallIntegerField(
        default=3,
        help_text="Maximum number of cards to show (newest / highest priority first).",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Homepage events settings"
        verbose_name_plural = "Homepage events settings"

    def __str__(self) -> str:
        return "Homepage events settings"

    @classmethod
    def load(cls):
        """Return the settings row editors manage in Snippets (same pattern as Global Solutions)."""
        obj = cls.objects.order_by("pk").first()
        if obj:
            return obj
        return cls.objects.create(
            section_enabled=False,
            section_eyebrow="What's next",
            section_title="Upcoming events & announcements",
            section_lead=(
                "Join us in the field, online, and in community — "
                "dates and highlights worth marking on your calendar."
            ),
            max_items=3,
        )

    panels = [
        MultiFieldPanel(
            [
                HelpPanel(
                    content=(
                        "<p><strong>Main site homepage</strong> — section appears after "
                        "<em>Latest Updates</em>, before the Global Solutions promo card.</p>"
                        "<p>Turn <strong>Section enabled</strong> off to hide the entire block "
                        "without deleting individual items.</p>"
                    ),
                ),
                FieldPanel("section_enabled"),
                FieldPanel("section_eyebrow"),
                FieldPanel("section_title"),
                FieldPanel("section_lead"),
                FieldPanel("max_items"),
            ],
            heading="Homepage events section",
        ),
    ]


@register_snippet
class HomepageEvent(models.Model):
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this item without deleting it.",
    )
    kind = models.CharField(
        max_length=20,
        choices=HomepageEventKind.choices,
        default=HomepageEventKind.EVENT,
    )
    title = models.CharField(max_length=200)
    event_date = models.DateField(
        blank=True,
        null=True,
        help_text="Optional. Shown at the top of the card, e.g. August 29.",
    )
    event_time_label = models.CharField(
        max_length=80,
        blank=True,
        default="",
        help_text='Optional time text, e.g. "6:00 pm" or "All day".',
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Short paragraph (1–3 sentences).",
    )
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Optional card image (640×360 or wider recommended).",
    )
    video = models.ForeignKey(
        "wagtaildocs.Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Optional MP4 or WebM clip shown below the description on the card.",
    )
    link = models.CharField(
        max_length=300,
        blank=True,
        default="",
        help_text="Where the button goes. Leave blank to hide the button.",
    )
    button_text = models.CharField(
        max_length=80,
        blank=True,
        default="Learn more",
    )
    starts_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text=(
            "Optional. When the card first appears on the homepage. "
            "Leave blank to show immediately (recommended for upcoming events)."
        ),
    )
    ends_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text=(
            "Optional. Hide the card after this date/time "
            "(e.g. the day after your event ends)."
        ),
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "event_date", "-created_at"]
        verbose_name = "Homepage event / announcement"
        verbose_name_plural = "Homepage events & announcements"

    def __str__(self) -> str:
        return self.title

    @property
    def is_visible_now(self) -> bool:
        if not self.is_active:
            return False
        now = timezone.now()
        if self.starts_at and self.starts_at > now:
            return False
        if self.ends_at and self.ends_at < now:
            return False
        return True

    @property
    def formatted_date_line(self) -> str:
        if self.event_date:
            line = date_format(self.event_date, "F j")
            time_label = (self.event_time_label or "").strip()
            if time_label:
                return f"{line} @ {time_label}"
            return line
        return (self.event_time_label or "").strip()

    @property
    def card_image_url(self) -> str:
        return _wagtail_image_rendition_url(self.image)

    @property
    def button_label(self) -> str:
        label = (self.button_text or "").strip()
        return label or "Learn more"

    @property
    def has_link(self) -> bool:
        return bool((self.link or "").strip())

    @property
    def has_video(self) -> bool:
        return bool(self.video_id)

    @property
    def video_url(self) -> str:
        if not self.video_id:
            return ""
        try:
            return self.video.url
        except Exception:
            file_obj = getattr(self.video, "file", None)
            return file_obj.url if file_obj else ""

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("is_active"),
                FieldPanel("kind"),
                FieldPanel("sort_order"),
            ],
            heading="Visibility",
        ),
        MultiFieldPanel(
            [
                FieldPanel("title"),
                FieldPanel("event_date"),
                FieldPanel("event_time_label"),
                FieldPanel("description"),
                FieldPanel("image"),
                FieldPanel("video"),
            ],
            heading="Content",
        ),
        MultiFieldPanel(
            [
                FieldPanel("link"),
                FieldPanel("button_text"),
                FieldPanel("starts_at"),
                FieldPanel("ends_at"),
            ],
            heading="Link & schedule",
        ),
    ]

    @classmethod
    def get_visible(cls, *, limit: int = 3):
        now = timezone.now()
        qs = cls.objects.filter(is_active=True)
        qs = qs.filter(models.Q(starts_at__isnull=True) | models.Q(starts_at__lte=now))
        qs = qs.filter(models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=now))
        return qs.order_by("sort_order", "event_date", "-created_at")[:limit]


def get_homepage_events_for_context():
    settings = HomepageEventsSettings.load()
    if not settings.section_enabled:
        return None
    limit = max(1, min(settings.max_items or 3, 12))
    events = list(HomepageEvent.get_visible(limit=limit))
    if not events:
        return None
    return {"settings": settings, "events": events}
