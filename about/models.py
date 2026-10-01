from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.search import index


class AboutPage(Page):
    """Fixed-layout About page. Editors change the copy, photo, and links only."""

    template = "about/about_page.html"
    max_count = 1
    subpage_types = []

    organization_name = models.CharField(
        max_length=120,
        default="Yeshua Life Limited",
        help_text="Small line above the page title.",
    )
    lead = models.TextField(
        help_text="Short introduction under the title.",
    )
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Leave empty to keep the current Karamoja photograph.",
    )
    image_alt = models.CharField(
        max_length=200,
        blank=True,
        default="Agricultural work supported by Yeshua Life in Karamoja",
    )
    image_caption = models.CharField(
        max_length=200,
        blank=True,
        default="Karamoja, Uganda",
    )
    organization_heading = models.CharField(
        max_length=80,
        default="The organization",
    )
    body = RichTextField()
    work_heading = models.CharField(max_length=80, default="Areas of work")
    office_heading = models.CharField(max_length=80, default="Office")
    address = models.TextField(
        help_text="Line breaks are kept.",
    )
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    primary_label = models.CharField(max_length=40, blank=True, default="Contact")
    primary_url = models.CharField(
        max_length=200,
        blank=True,
        default="/contact/",
        help_text="Path on this site, such as /contact/",
    )
    secondary_label = models.CharField(max_length=40, blank=True, default="Pay online")
    secondary_url = models.CharField(
        max_length=200,
        blank=True,
        default="/payments",
    )

    search_fields = Page.search_fields + [
        index.SearchField("lead"),
        index.SearchField("body"),
        index.SearchField("address"),
    ]

    content_panels = [
        FieldPanel(
            "title",
            help_text="Large heading on the page. The public address stays /about/.",
        ),
        MultiFieldPanel(
            [
                FieldPanel("organization_name"),
                FieldPanel("lead"),
            ],
            heading="Introduction",
        ),
        MultiFieldPanel(
            [
                FieldPanel("hero_image"),
                FieldPanel("image_alt"),
                FieldPanel("image_caption"),
            ],
            heading="Photograph",
        ),
        MultiFieldPanel(
            [
                FieldPanel("organization_heading"),
                FieldPanel("body"),
            ],
            heading="The organization",
        ),
        MultiFieldPanel(
            [FieldPanel("work_heading")],
            heading="Areas of work",
        ),
        InlinePanel("work_areas", label="Area of work"),
        MultiFieldPanel(
            [
                FieldPanel("office_heading"),
                FieldPanel("address"),
                FieldPanel("phone"),
                FieldPanel("email"),
                FieldPanel("primary_label"),
                FieldPanel("primary_url"),
                FieldPanel("secondary_label"),
                FieldPanel("secondary_url"),
            ],
            heading="Office",
        ),
    ]

    class Meta:
        verbose_name = "About page"

    def clean(self):
        self.slug = "about"
        super().clean()

    def phone_href(self):
        digits = "".join(ch for ch in (self.phone or "") if ch.isdigit() or ch == "+")
        return f"tel:{digits}" if digits else ""


class AboutWorkArea(Orderable):
    page = ParentalKey(
        AboutPage,
        on_delete=models.CASCADE,
        related_name="work_areas",
    )
    title = models.CharField(max_length=80)
    summary = models.TextField()
    url = models.CharField(
        max_length=200,
        blank=True,
        help_text="Path on this site, such as /karamoja. Leave empty for a line with no link.",
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("summary"),
        FieldPanel("url"),
    ]
