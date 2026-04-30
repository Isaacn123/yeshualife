from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


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


class GlobalSolutionsBlockCategory(models.TextChoices):
    WEALTH_CREATION = "wealth_creation", "Wealth Creation"
    HEALINGS = "healings", "Healings"
    INNOVATIONS = "innovations", "Innovations"
    ADVANCEMENT = "advancement", "Advancement"
    INTEGRATION = "integration", "Integration"
    POWER = "power", "Power"
    EDUCATION = "education", "Education"
    KNOWLEDGE = "knowledge", "Knowledge"


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


class GlobalSolutionsVideoKind(models.TextChoices):
    FEEDING = "feeding", "Feeding"
    PREACHING = "preaching", "Preachings"
    LEARNING = "learning", "Learning"


class GlobalSolutionsVideoStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    UPLOADING = "uploading", "Uploading"
    UPLOADED = "uploaded", "Uploaded"
    PROCESSING = "processing", "Processing"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"


class GlobalSolutionsVideo(models.Model):
    """
    Stores metadata + B2 object keys/URLs for a single uploaded clip.
    Upload flow (recommended):
      1) Create record (status=UPLOADING) -> get presigned multipart URLs
      2) Browser uploads directly to B2
      3) Complete multipart -> status=UPLOADED
      4) Background ffmpeg transcodes to HLS -> uploads to B2 -> status=READY
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    kind = models.CharField(max_length=16, choices=GlobalSolutionsVideoKind.choices)
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
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "sort_order", "-created_at"]
        indexes = [
            models.Index(fields=["kind", "is_active", "published_at"]),
            models.Index(fields=["status", "updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()}: {self.title}"

