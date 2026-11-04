import django.db.models.deletion
import django.utils.timezone
import uuid
import wagtail.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("karamoja_response", "0003_karamojaresponseindexpage_image"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResponsePageVideo",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("title", models.CharField(default="Untitled video", max_length=200)),
                ("slug", models.SlugField(blank=True, max_length=220, unique=True)),
                ("description", wagtail.fields.RichTextField(blank=True)),
                ("views", models.PositiveIntegerField(default=0)),
                ("likes", models.PositiveIntegerField(default=0)),
                ("shares", models.PositiveIntegerField(default=0)),
                ("published_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("original_b2_key", models.CharField(blank=True, default="", max_length=512)),
                (
                    "original_content_type",
                    models.CharField(blank=True, default="", max_length=128),
                ),
                ("original_size_bytes", models.BigIntegerField(blank=True, null=True)),
                ("poster_image_url", models.URLField(blank=True, default="")),
                ("poster_b2_key", models.CharField(blank=True, default="", max_length=512)),
                ("duration_seconds", models.PositiveIntegerField(blank=True, null=True)),
                ("resolution_label", models.CharField(blank=True, default="", max_length=16)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("uploading", "Uploading"),
                            ("ready", "Ready"),
                            ("failed", "Failed"),
                        ],
                        default="draft",
                        max_length=16,
                    ),
                ),
                ("last_error", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "page",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="response_videos",
                        to="karamoja_response.karamojaresponsepage",
                    ),
                ),
            ],
            options={
                "verbose_name": "Response page video",
                "verbose_name_plural": "Response page videos",
                "ordering": ["sort_order", "-published_at", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="responsepagevideo",
            index=models.Index(
                fields=["page", "is_active", "status", "sort_order"],
                name="karamoja_re_page_id_7d1c2a_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="responsepagevideo",
            index=models.Index(fields=["slug"], name="karamoja_re_slug_0f3b9e_idx"),
        ),
    ]
