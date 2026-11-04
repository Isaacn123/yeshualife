"""Page-attached response videos (B2 upload, thumbnails, views, likes)."""

from __future__ import annotations

import uuid

from django.conf import settings as django_settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from wagtail.fields import RichTextField


def _unique_slug(model_cls, base: str, *, exclude_pk=None) -> str:
    base = slugify(base)[:200] or "video"
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


class ResponsePageVideoStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    UPLOADING = "uploading", "Uploading"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"


class ResponsePageVideo(models.Model):
    """
    Video attached to a Karamoja Response page.

    Upload goes straight to Backblaze B2 (same stack as Global Solutions).
    Playback is progressive MP4; thumbnails are chosen in the admin panel.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.ForeignKey(
        "karamoja_response.karamojaResponsePage",
        on_delete=models.CASCADE,
        related_name="response_videos",
    )
    title = models.CharField(max_length=200, default="Untitled video")
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = RichTextField(blank=True)

    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)

    published_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    original_b2_key = models.CharField(max_length=512, blank=True, default="")
    original_content_type = models.CharField(max_length=128, blank=True, default="")
    original_size_bytes = models.BigIntegerField(null=True, blank=True)
    poster_image_url = models.URLField(blank=True, default="")
    poster_b2_key = models.CharField(max_length=512, blank=True, default="")
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    resolution_label = models.CharField(max_length=16, blank=True, default="")

    status = models.CharField(
        max_length=16,
        choices=ResponsePageVideoStatus.choices,
        default=ResponsePageVideoStatus.DRAFT,
    )
    last_error = models.TextField(blank=True, default="")

    created_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Duck-typed for global_solutions.thumbnails helpers
    parent_video_id = None

    class Meta:
        ordering = ["sort_order", "-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["page", "is_active", "status", "sort_order"]),
            models.Index(fields=["slug"]),
        ]
        verbose_name = "Response page video"
        verbose_name_plural = "Response page videos"

    def __str__(self) -> str:
        return f"{self.title} ({self.page_id})"

    @property
    def storage_path_slug(self) -> str:
        return "karamoja-response"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(ResponsePageVideo, self.title, exclude_pk=self.pk)
        if (self.poster_b2_key or "").strip():
            self.poster_image_url = ""
        super().save(*args, **kwargs)

    @property
    def thumbnail_url(self) -> str:
        key = (self.poster_b2_key or "").strip()
        if key:
            from global_solutions.thumbnails import poster_url_for_key

            return poster_url_for_key(key)
        from global_solutions.b2 import ensure_absolute_url

        return ensure_absolute_url((self.poster_image_url or "").strip())

    @property
    def playback_url(self) -> str:
        from global_solutions.b2 import b2_presigned_get_url, b2_public_url

        if not self.original_b2_key:
            return ""
        if getattr(django_settings, "B2_PLAYBACK_USE_PRESIGNED", True):
            content_type = (self.original_content_type or "video/mp4").strip() or "video/mp4"
            return b2_presigned_get_url(
                self.original_b2_key,
                expires_in=getattr(django_settings, "B2_PLAYBACK_PRESIGNED_EXPIRES", 86400),
                response_content_type=content_type,
            )
        return b2_public_url(self.original_b2_key)

    @property
    def duration_display(self) -> str:
        if not self.duration_seconds:
            return ""
        m, s = divmod(int(self.duration_seconds), 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    @staticmethod
    def _count_display(n: int) -> str:
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
        if n >= 1_000:
            return f"{n / 1_000:.1f}k".replace(".0k", "k")
        return str(n)

    @property
    def views_display(self) -> str:
        return self._count_display(self.views)

    @property
    def likes_display(self) -> str:
        return self._count_display(self.likes)

    @property
    def shares_display(self) -> str:
        return self._count_display(self.shares)

    def get_absolute_url(self) -> str:
        try:
            base = self.page.url or "/"
        except Exception:
            base = "/"
        return f"{base}#video-{self.slug}"

    @classmethod
    def ready_for_page(cls, page):
        return cls.objects.filter(
            page=page,
            is_active=True,
            status=ResponsePageVideoStatus.READY,
        ).exclude(original_b2_key="").order_by("sort_order", "-published_at")
