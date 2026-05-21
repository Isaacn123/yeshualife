# Generated manually: dynamic video categories (snippets)

from django.db import migrations, models
import django.db.models.deletion


def seed_categories_and_migrate_kind(apps, schema_editor):
    Category = apps.get_model("global_solutions", "GlobalSolutionsVideoCategory")
    Video = apps.get_model("global_solutions", "GlobalSolutionsVideo")

    defaults = [
        {
            "slug": "feeding",
            "name": "Feeding",
            "heading_upper": "{count} clips",
            "section_intro": "Community meals and feeding outreach — fresh clips uploaded from the field.",
            "title_align": "right",
            "sort_order": 10,
        },
        {
            "slug": "preaching",
            "name": "Preachings",
            "heading_upper": "{count} clips",
            "section_intro": "Messages and ministry.",
            "title_align": "left",
            "sort_order": 20,
        },
        {
            "slug": "learning",
            "name": "Learning",
            "heading_upper": "{count} clips",
            "section_intro": "Teaching and training clips.",
            "title_align": "right",
            "sort_order": 30,
        },
    ]
    by_slug = {}
    for row in defaults:
        cat, _ = Category.objects.get_or_create(slug=row["slug"], defaults=row)
        for key, val in row.items():
            setattr(cat, key, val)
        cat.save()
        by_slug[row["slug"]] = cat

    for video in Video.objects.all():
        old_kind = getattr(video, "kind", None) or ""
        cat = by_slug.get(old_kind)
        if cat:
            video.category_id = cat.pk
            video.save(update_fields=["category_id"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("global_solutions", "0003_globalsolutionspage_and_index_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="GlobalSolutionsVideoCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="Shown in admin and on the public page (section title).", max_length=120)),
                ("slug", models.SlugField(help_text="URL-safe id (e.g. feeding). Used for uploads and section anchors.", max_length=32, unique=True)),
                ("heading_upper", models.CharField(blank=True, default="", help_text="Small line above the title. Use {count} for number of clips (e.g. “{count} clips”).", max_length=160)),
                ("section_intro", models.TextField(blank=True, default="", help_text="Default text in the description box when a clip has no description.")),
                ("title_align", models.CharField(choices=[("right", "Title box — right"), ("left", "Title box — left")], default="right", max_length=16)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Video category",
                "verbose_name_plural": "Video categories",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.AddField(
            model_name="globalsolutionsvideo",
            name="category",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="videos",
                to="global_solutions.globalsolutionsvideocategory",
                verbose_name="Kind",
            ),
        ),
        migrations.RunPython(seed_categories_and_migrate_kind, noop_reverse),
        migrations.RemoveField(
            model_name="globalsolutionsvideo",
            name="kind",
        ),
        migrations.AlterField(
            model_name="globalsolutionsvideo",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="videos",
                to="global_solutions.globalsolutionsvideocategory",
                verbose_name="Kind",
            ),
        ),
        migrations.RemoveIndex(
            model_name="globalsolutionsvideo",
            name="global_solut_kind_dbbbae_idx",
        ),
        migrations.AddIndex(
            model_name="globalsolutionsvideo",
            index=models.Index(
                fields=["category", "is_active", "published_at"],
                name="gs_video_cat_pub_idx",
            ),
        ),
    ]
