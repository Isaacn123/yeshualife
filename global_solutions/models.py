from __future__ import annotations

import uuid

from django.conf import settings as django_settings
from django.db import models
from django.utils import timezone

from django.utils.html import format_html

from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from .wagtail_panels import GlobalSolutionsVideoB2UploadPanel


def _video_slides_meta(videos: list) -> list[dict[str, str]]:
    return [
        {"title": (v.title or "").strip(), "description": (v.description or "").strip()}
        for v in videos
    ]


def build_global_solutions_public_context() -> dict:
    """Template context for the public Global Solutions index page (videos, hero)."""
    settings_obj = GlobalSolutionsSettings.objects.first()
    page_title = (settings_obj.page_title if settings_obj else "Global Solutions").strip() or "Global Solutions"
    hero_title = (settings_obj.hero_title if settings_obj else page_title).strip() or page_title
    hero_subtitle = (settings_obj.hero_subtitle if settings_obj else "").strip()

    videos_qs = GlobalSolutionsVideo.objects.filter(
        is_active=True,
        status=GlobalSolutionsVideoStatus.READY,
    ).select_related("category")
    cap = int(getattr(django_settings, "GLOBAL_SOLUTIONS_PUBLIC_VIDEO_CAP", 72))

    video_sections = []
    categories = GlobalSolutionsVideoCategory.objects.filter(is_active=True).order_by(
        "sort_order", "name"
    )
    for category in categories:
        cat_qs = videos_qs.filter(category=category).order_by("-published_at", "sort_order")
        total = cat_qs.count()
        videos = list(cat_qs[:cap])
        if not videos:
            continue
        video_sections.append(
            {
                "category": category,
                "videos": videos,
                "total_count": total,
                "heading_upper": category.heading_upper_display(total),
                "slides_meta": _video_slides_meta(videos),
                "carousel_id": f"gs-carousel-{category.slug}",
                "description_target": f"gs-slide-description-{category.slug}",
                "description_meta_id": f"{category.slug}-slides-meta",
            }
        )

    has_any_videos = bool(video_sections)

    return {
        "hero_title": hero_title,
        "hero_subtitle": hero_subtitle,
        "hero_image_url": (settings_obj.hero_image_url if settings_obj else "").strip(),
        "video_sections": video_sections,
        "global_solutions_video_cap": cap,
        "has_any_videos": has_any_videos,
    }


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
            models.Index(
                fields=["category", "is_active", "sort_order"],
                name="global_solut_category_7d69cf_idx",
            ),
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


class GlobalSolutionsVideoCategoryAlign(models.TextChoices):
    RIGHT = "right", "Title box — right"
    LEFT = "left", "Title box — left"


@register_snippet
class GlobalSolutionsVideoCategory(models.Model):
    """
    Manage video types (Kind) from Snippets — add, edit, delete, reorder.
    """

    name = models.CharField(max_length=120, help_text="Shown in admin and on the public page (section title).")
    slug = models.SlugField(
        max_length=32,
        unique=True,
        help_text="URL-safe id (e.g. feeding). Used for uploads and section anchors.",
    )
    heading_upper = models.CharField(
        max_length=160,
        blank=True,
        default="",
        help_text="Small line above the title. Use {count} for number of clips (e.g. “{count} clips”).",
    )
    section_intro = models.TextField(
        blank=True,
        default="",
        help_text="Default text in the description box when a clip has no description.",
    )
    title_align = models.CharField(
        max_length=16,
        choices=GlobalSolutionsVideoCategoryAlign.choices,
        default=GlobalSolutionsVideoCategoryAlign.RIGHT,
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Video category"
        verbose_name_plural = "Video categories"

    def __str__(self) -> str:
        return self.name

    def heading_upper_display(self, count: int) -> str:
        template = (self.heading_upper or "").strip()
        if template:
            return template.replace("{count}", str(count))
        if count:
            return f"{count} clip{'s' if count != 1 else ''}"
        return "Community outreach"

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("heading_upper"),
        FieldPanel("section_intro"),
        FieldPanel("title_align"),
        FieldPanel("sort_order"),
        FieldPanel("is_active"),
    ]


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

    category = models.ForeignKey(
        GlobalSolutionsVideoCategory,
        on_delete=models.PROTECT,
        related_name="videos",
        verbose_name="Kind",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")

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
            models.Index(
                fields=["category", "is_active", "published_at"],
                name="global_solut_category_vid_idx",
            ),
            models.Index(
                fields=["status", "updated_at"],
                name="global_solut_status_d87a65_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.category}: {self.title}"

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
                FieldPanel("title"),
                FieldPanel("description"),
                FieldPanel("published_at"),
                FieldPanel("is_active"),
                FieldPanel("sort_order"),
            ],
            heading="Details",
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

    template = "global_solutions/global_solutions_page.html"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context.update(build_global_solutions_public_context())
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

