# FarmHub: SolutionCategory + Creator snippets; replace hardcoded video kind with category FK.

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models
from django.utils.text import slugify


DEFAULT_CATEGORIES = [
    ("feeding", "Feeding", "Community meals and feeding outreach", 0, True),
    ("preaching", "Preachings", "Messages and ministry", 1, True),
    ("learning", "Learning", "Teaching and training clips", 2, True),
    ("agriculture", "Agriculture", "General farming and cultivation", 10, True),
    ("crop-farming", "Crop Farming", "Maize, beans, and field crops", 11, True),
    ("livestock", "Livestock", "Cattle, goats, and animal husbandry", 12, True),
    ("poultry", "Poultry", "Chickens and egg production", 13, True),
    ("irrigation", "Irrigation", "Water systems and drip irrigation", 14, True),
    ("machinery", "Machinery", "Tractors, harvesters, and equipment", 15, True),
    ("health", "Health", "Community health and wellness", 20, False),
    ("community", "Community", "Community development and outreach", 21, False),
]


def _unique_video_slug(Video, title, exclude_pk=None):
    base = slugify(title)[:200] or "video"
    slug = base
    n = 2
    while True:
        qs = Video.objects.filter(slug=slug)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        if not qs.exists():
            return slug
        slug = f"{base}-{n}"
        n += 1


def seed_categories_and_migrate_kind(apps, schema_editor):
    SolutionCategory = apps.get_model("global_solutions", "SolutionCategory")
    Video = apps.get_model("global_solutions", "GlobalSolutionsVideo")

    for slug, name, description, sort_order, show_on_home in DEFAULT_CATEGORIES:
        SolutionCategory.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "description": description,
                "sort_order": sort_order,
                "is_active": True,
                "show_on_home": show_on_home,
            },
        )

    slug_to_pk = {c.slug: c.pk for c in SolutionCategory.objects.all()}
    fallback_pk = slug_to_pk.get("feeding") or next(iter(slug_to_pk.values()), None)

    for video in Video.objects.all().iterator():
        kind = getattr(video, "kind", "") or ""
        if kind in slug_to_pk:
            video.category_id = slug_to_pk[kind]
        elif not video.category_id and fallback_pk:
            video.category_id = fallback_pk
        if not video.slug:
            video.slug = _unique_video_slug(Video, video.title, exclude_pk=video.pk)
        video.save(update_fields=["category_id", "slug"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("global_solutions", "0004_restore_video_kind"),
        ("wagtailimages", "0025_alter_image_file_alter_rendition_file"),
    ]

    operations = [
        migrations.CreateModel(
            name="SolutionCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("description", models.TextField(blank=True, default="")),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("show_on_home", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Solution category",
                "verbose_name_plural": "Solution categories",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="Creator",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("bio", models.TextField(blank=True, default="")),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "avatar",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="wagtailimages.image",
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.AddField(
            model_name="globalsolutionsvideo",
            name="slug",
            field=models.SlugField(blank=True, max_length=220),
        ),
        migrations.AddField(
            model_name="globalsolutionsvideo",
            name="tags",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Comma-separated tags for search (e.g. maize, irrigation, dairy).",
                max_length=500,
            ),
        ),
        migrations.AddField(
            model_name="globalsolutionsvideo",
            name="views",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="globalsolutionsvideo",
            name="featured",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="globalsolutionsvideo",
            name="resolution_label",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Display label e.g. 720p (filled by transcoder when available).",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="globalsolutionsvideo",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="videos",
                to="global_solutions.solutioncategory",
            ),
        ),
        migrations.AddField(
            model_name="globalsolutionsvideo",
            name="creator",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="videos",
                to="global_solutions.creator",
            ),
        ),
        migrations.RunPython(seed_categories_and_migrate_kind, noop_reverse),
        migrations.AlterField(
            model_name="globalsolutionsvideo",
            name="slug",
            field=models.SlugField(blank=True, max_length=220, unique=True),
        ),
        migrations.RemoveIndex(
            model_name="globalsolutionsvideo",
            name="global_solut_kind_dbbbae_idx",
        ),
        migrations.RemoveField(
            model_name="globalsolutionsvideo",
            name="kind",
        ),
        migrations.AlterField(
            model_name="globalsolutionsvideo",
            name="category",
            field=models.ForeignKey(
                help_text="Managed under Snippets → Solution categories (e.g. Feeding, Preaching, Crop Farming).",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="videos",
                to="global_solutions.solutioncategory",
            ),
        ),
        migrations.AddIndex(
            model_name="globalsolutionsvideo",
            index=models.Index(fields=["slug"], name="global_solut_slug_idx"),
        ),
        migrations.AddIndex(
            model_name="globalsolutionsvideo",
            index=models.Index(fields=["featured", "is_active", "published_at"], name="global_solut_feat_idx"),
        ),
        migrations.AddIndex(
            model_name="globalsolutionsvideo",
            index=models.Index(fields=["category", "is_active", "published_at"], name="global_solut_cat_pub_idx"),
        ),
    ]
