from __future__ import annotations

import uuid

from django.conf import settings as django_settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from django.utils.html import format_html

from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from .wagtail_panels import GlobalSolutionsVideoB2UploadPanel


def _unique_slug(model_cls, base: str, *, exclude_pk=None) -> str:
    base = slugify(base)[:200] or "item"
    slug = base
    n = 2
    while True:
        qs = model_cls.objects.filter(slug=slug)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        if not qs.exists():
            return slug
        slug = f"{base}-{n}"
        n += 1


@register_snippet
class GlobalSolutionsSettings(models.Model):
    """
    Singleton-ish settings for the Global Solutions page.
    (We enforce a single row in admin by convention.)
    """

    page_title = models.CharField(max_length=160, default="Global Solutions")
    hero_title = models.CharField(max_length=160, default="Global Solutions")
    hero_subtitle = models.TextField(blank=True, default="")
    hero_image_url = models.URLField(blank=True, default="")

    seo_description = models.CharField(max_length=300, blank=True, default="")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Global Solutions Page Settings"
        verbose_name_plural = "Global Solutions Page Settings"

    def __str__(self) -> str:
        return "Global Solutions Settings"

    panels = [
        FieldPanel("page_title"),
        FieldPanel("hero_title"),
        FieldPanel("hero_subtitle"),
        FieldPanel("hero_image_url"),
        FieldPanel("seo_description"),
    ]


class GlobalSolutionsBlockCategory(models.TextChoices):
    WEALTH_CREATION = "wealth_creation", "Wealth Creation"
    HEALINGS = "healings", "Healings"
    INNOVATIONS = "innovations", "Innovations"
    ADVANCEMENT = "advancement", "Advancement"
    INTEGRATION = "integration", "Integration"
    POWER = "power", "Power"
    EDUCATION = "education", "Education"
    KNOWLEDGE = "knowledge", "Knowledge"


@register_snippet
class GlobalSolutionsBlock(models.Model):
    category = models.CharField(max_length=32, choices=GlobalSolutionsBlockCategory.choices)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True, default="")
    image_url = models.URLField(blank=True, default="")
    link_url = models.URLField(blank=True, default="")

    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "sort_order", "-created_at"]
        indexes = [
            models.Index(fields=["category", "is_active", "sort_order"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_category_display()}: {self.title}"

    panels = [
        FieldPanel("category"),
        FieldPanel("title"),
        FieldPanel("body"),
        FieldPanel("image_url"),
        FieldPanel("link_url"),
        FieldPanel("sort_order"),
        FieldPanel("is_active"),
    ]


@register_snippet
class SolutionCategory(models.Model):
    """FarmHub taxonomy — managed in Wagtail Snippets."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    show_on_home = models.BooleanField(
        default=True,
        help_text="Show as a carousel row on the FarmHub homepage.",
    )

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Solution category"
        verbose_name_plural = "Solution categories"

    def __str__(self) -> str:
        return self.name

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("description"),
        FieldPanel("sort_order"),
        FieldPanel("is_active"),
        FieldPanel("show_on_home"),
    ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(SolutionCategory, self.name, exclude_pk=self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("global_solutions:farmhub_category", kwargs={"slug": self.slug})


@register_snippet
class Creator(models.Model):
    """Farmer, extension officer, or ministry channel profile."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=120, unique=True)
    bio = models.TextField(blank=True, default="")
    avatar = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("bio"),
        FieldPanel("avatar"),
        FieldPanel("sort_order"),
        FieldPanel("is_active"),
    ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Creator, self.name, exclude_pk=self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("global_solutions:farmhub_creator", kwargs={"slug": self.slug})


class GlobalSolutionsVideoStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    UPLOADING = "uploading", "Uploading"
    UPLOADED = "uploaded", "Uploaded"
    PROCESSING = "processing", "Processing"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"


@register_snippet
class GlobalSolutionsVideo(models.Model):
    """
    Stores metadata + B2 object keys/URLs for a single uploaded clip.

    Default (GLOBAL_SOLUTIONS_TRANSCODE_HLS unset/false): multipart complete -> READY; playback uses progressive MP4.
    HLS mode (GLOBAL_SOLUTIONS_TRANSCODE_HLS=true): complete -> UPLOADED -> PROCESSING -> manage.py process_* -> READY + HLS URLs.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    tags = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Comma-separated tags for search (e.g. maize, irrigation, dairy).",
    )

    category = models.ForeignKey(
        SolutionCategory,
        on_delete=models.PROTECT,
        related_name="videos",
        help_text="Managed under Snippets → Solution categories (e.g. Feeding, Preaching, Crop Farming).",
    )
    creator = models.ForeignKey(
        Creator,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="videos",
    )

    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    featured = models.BooleanField(default=False)
    resolution_label = models.CharField(
        max_length=16,
        blank=True,
        default="",
        help_text="Display label e.g. 720p (filled by transcoder when available).",
    )

    published_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    # Original upload (B2)
    original_b2_key = models.CharField(max_length=512, blank=True, default="")
    original_content_type = models.CharField(max_length=128, blank=True, default="")
    original_size_bytes = models.BigIntegerField(null=True, blank=True)

    # HLS output (B2)
    hls_master_manifest_key = models.CharField(max_length=512, blank=True, default="")
    hls_master_manifest_url = models.URLField(blank=True, default="")
    poster_image_url = models.URLField(blank=True, default="")
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)

    status = models.CharField(
        max_length=16, choices=GlobalSolutionsVideoStatus.choices, default=GlobalSolutionsVideoStatus.DRAFT
    )
    last_error = models.TextField(blank=True, default="")

    created_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "sort_order", "-created_at"]
        indexes = [
            models.Index(fields=["status", "updated_at"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["featured", "is_active", "published_at"]),
            models.Index(fields=["category", "is_active", "published_at"]),
        ]

    def __str__(self) -> str:
        cat = self.category.name if self.category_id else "Uncategorized"
        return f"{cat}: {self.title}"

    @property
    def storage_path_slug(self) -> str:
        if self.category_id:
            return self.category.slug
        return "uncategorized"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(GlobalSolutionsVideo, self.title, exclude_pk=self.pk)
        super().save(*args, **kwargs)

    @property
    def tags_list(self) -> list[str]:
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    @property
    def thumbnail_url(self) -> str:
        return (self.poster_image_url or "").strip()

    @property
    def duration_display(self) -> str:
        if not self.duration_seconds:
            return ""
        m, s = divmod(int(self.duration_seconds), 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    @property
    def views_display(self) -> str:
        return self._count_display(self.views)

    @property
    def likes_display(self) -> str:
        return self._count_display(self.likes)

    @staticmethod
    def _count_display(n: int) -> str:
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
        if n >= 1_000:
            return f"{n / 1_000:.1f}k".replace(".0k", "k")
        return str(n)

    def get_absolute_url(self) -> str:
        return reverse("global_solutions:farmhub_video", kwargs={"slug": self.slug})

    @property
    def playback_url(self) -> str:
        """HLS manifest URL when set; else progressive MP4 (presigned GET by default for private buckets)."""
        from .b2 import b2_presigned_get_url, b2_public_url

        hls = (self.hls_master_manifest_url or "").strip()
        if hls:
            return hls
        if not self.original_b2_key:
            return ""
        if getattr(django_settings, "B2_PLAYBACK_USE_PRESIGNED", True):
            return b2_presigned_get_url(
                self.original_b2_key,
                expires_in=getattr(django_settings, "B2_PLAYBACK_PRESIGNED_EXPIRES", 86400),
            )
        return b2_public_url(self.original_b2_key)

    @property
    def playback_uses_hls(self) -> bool:
        u = (self.hls_master_manifest_url or "").strip().lower()
        return bool(u and ".m3u8" in u)

    panels = [
        HelpPanel(
            heading="How this video works",
            content=(
                format_html(
                    "<p>Videos are stored in Backblaze B2. After multipart upload completes they become "
                    "<strong>Ready</strong> automatically and play from your uploaded file (progressive MP4). "
                    "By default playback uses <strong>presigned URLs</strong> so private buckets work; set "
                    "<code>B2_PLAYBACK_USE_PRESIGNED=false</code> only if files are fully public. "
                    "Keep bucket CORS allowing your site for <code>s3_get</code> / reads so the browser can stream.</p>"
                    '<p>Optional: use the <a href="{}">standalone upload center</a>.</p>'
                    '<p>To use HLS transcoding instead, set environment variable '
                    "<code>GLOBAL_SOLUTIONS_TRANSCODE_HLS=true</code> and run "
                    "<code>python manage.py process_global_solutions_videos</code> on the server (or on a schedule).</p>",
                    "/global-solutions/upload/",
                )
                if not getattr(django_settings, "GLOBAL_SOLUTIONS_TRANSCODE_HLS", False)
                else format_html(
                    "<p>HLS transcoding is enabled. Upload completes with status <strong>Uploaded</strong>; "
                    "click <strong>Mark for processing</strong>, then run "
                    "<code>python manage.py process_global_solutions_videos</code> on the server (or schedule it). "
                    "Manifest, poster, and duration are filled after transcoding.</p>"
                    '<p>You can also use the <a href="{}">standalone upload center</a>.</p>',
                    "/global-solutions/upload/",
                )
            ),
        ),
        MultiFieldPanel(
            [
                FieldPanel("category"),
                FieldPanel("creator"),
                FieldPanel("title"),
                FieldPanel("slug"),
                FieldPanel("description"),
                FieldPanel("tags"),
                FieldPanel("featured"),
                FieldPanel("published_at"),
                FieldPanel("is_active"),
                FieldPanel("sort_order"),
            ],
            heading="Details",
        ),
        MultiFieldPanel(
            [
                FieldPanel("views", read_only=True),
                FieldPanel("likes", read_only=True),
                FieldPanel("resolution_label", read_only=True),
            ],
            heading="Discovery stats",
        ),
        GlobalSolutionsVideoB2UploadPanel(heading="Video upload"),
        MultiFieldPanel(
            [
                FieldPanel("status", read_only=True),
                FieldPanel("last_error", read_only=True),
                FieldPanel("original_b2_key", read_only=True),
                FieldPanel("original_content_type", read_only=True),
                FieldPanel("original_size_bytes", read_only=True),
                FieldPanel("hls_master_manifest_key", read_only=True),
                FieldPanel("hls_master_manifest_url", read_only=True),
                FieldPanel("poster_image_url", read_only=True),
                FieldPanel("duration_seconds", read_only=True),
            ],
            heading="Storage & playback (automatic)",
        ),
    ]


class GlobalSolutionsIndexPage(Page):
    """
    Parent page for the Global Solutions section (listing / hub).
    Hub body content still uses Global Solutions settings, blocks, and videos.
    """

    intro = models.CharField(max_length=200)
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.PROTECT,
        related_name="+",
        blank=True,
        null=True,
    )

    subpage_types = ["global_solutions.GlobalSolutionsPage"]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("image"),
    ]

    class Meta:
        verbose_name = "Global Solutions index page"

    template = "global_solutions/farmhub_home.html"

    def get_context(self, request, *args, **kwargs):
        from .discovery import build_farmhub_home_context

        context = super().get_context(request, *args, **kwargs)
        context.update(build_farmhub_home_context())
        # Child article pages (single-item views live at each child URL).
        context["global_solutions_articles"] = list(
            GlobalSolutionsPage.objects.child_of(self).live().public().order_by("-first_published_at")
        )
        return context


class GlobalSolutionsPage(Page):
    """Child article-style page under Global Solutions (same pattern as Awards page)."""

    # parent_page_types = ["global_solutions.GlobalSolutionsIndexPage"]

    date = models.DateField("Post date", null=True, blank=True)
    body = RichTextField(blank=True, null=True)
    intro = models.CharField(max_length=200)

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.PROTECT,
        related_name="+",
        blank=True,
        null=True,
    )
    caption = models.CharField(blank=True, max_length=250)

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("intro"),
        FieldPanel("body"),
        FieldPanel("image"),
        FieldPanel("caption"),
    ]

    class Meta:
        verbose_name = "Global Solutions page"

    # template = "global_solutions/global_solutions_detail_page.html"

