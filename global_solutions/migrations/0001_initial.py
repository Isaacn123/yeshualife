# Generated manually (initial migration) for the global_solutions app.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GlobalSolutionsSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("page_title", models.CharField(default="Global Solutions", max_length=160)),
                ("hero_title", models.CharField(default="Global Solutions", max_length=160)),
                ("hero_subtitle", models.TextField(blank=True, default="")),
                ("hero_image_url", models.URLField(blank=True, default="")),
                ("seo_description", models.CharField(blank=True, default="", max_length=300)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Global Solutions Page Settings",
                "verbose_name_plural": "Global Solutions Page Settings",
            },
        ),
        migrations.CreateModel(
            name="GlobalSolutionsBlock",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("wealth_creation", "Wealth Creation"),
                            ("healings", "Healings"),
                            ("innovations", "Innovations"),
                            ("advancement", "Advancement"),
                            ("integration", "Integration"),
                            ("power", "Power"),
                            ("education", "Education"),
                            ("knowledge", "Knowledge"),
                        ],
                        max_length=32,
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("body", models.TextField(blank=True, default="")),
                ("image_url", models.URLField(blank=True, default="")),
                ("link_url", models.URLField(blank=True, default="")),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["category", "sort_order", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="GlobalSolutionsVideo",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "kind",
                    models.CharField(choices=[("feeding", "Feeding"), ("preaching", "Preachings"), ("learning", "Learning")], max_length=16),
                ),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, default="")),
                ("published_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("original_b2_key", models.CharField(blank=True, default="", max_length=512)),
                ("original_content_type", models.CharField(blank=True, default="", max_length=128)),
                ("original_size_bytes", models.BigIntegerField(blank=True, null=True)),
                ("hls_master_manifest_key", models.CharField(blank=True, default="", max_length=512)),
                ("hls_master_manifest_url", models.URLField(blank=True, default="")),
                ("poster_image_url", models.URLField(blank=True, default="")),
                ("duration_seconds", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("uploading", "Uploading"),
                            ("uploaded", "Uploaded"),
                            ("processing", "Processing"),
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
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ["-published_at", "sort_order", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="globalsolutionsblock",
            index=models.Index(fields=["category", "is_active", "sort_order"], name="global_solut_category_7d69cf_idx"),
        ),
        migrations.AddIndex(
            model_name="globalsolutionsvideo",
            index=models.Index(fields=["kind", "is_active", "published_at"], name="global_solut_kind_dbbbae_idx"),
        ),
        migrations.AddIndex(
            model_name="globalsolutionsvideo",
            index=models.Index(fields=["status", "updated_at"], name="global_solut_status_d87a65_idx"),
        ),
    ]

