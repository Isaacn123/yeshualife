# Dynamic video categories (Wagtail snippets). Safe to re-run if a prior attempt
# stopped halfway (e.g. MySQL "table already exists").

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

    video_columns = _video_column_names(schema_editor)
    if "kind" not in video_columns:
        return

    for video in Video.objects.all():
        old_kind = getattr(video, "kind", None) or ""
        cat = by_slug.get(old_kind)
        if cat and not video.category_id:
            video.category_id = cat.pk
            video.save(update_fields=["category_id"])


def _video_column_names(schema_editor):
    connection = schema_editor.connection
    video_table = "global_solutions_globalsolutionsvideo"
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, video_table)
    return {col.name for col in description}


def _index_exists(schema_editor, table, index_name):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        constraints = connection.introspection.get_constraints(cursor, table)
    return index_name in constraints


def apply_videocategory_schema(apps, schema_editor):
    """Apply DB changes once; skip steps already done on a retry."""
    Category = apps.get_model("global_solutions", "GlobalSolutionsVideoCategory")
    Video = apps.get_model("global_solutions", "GlobalSolutionsVideo")
    connection = schema_editor.connection
    video_table = Video._meta.db_table
    cat_table = Category._meta.db_table
    tables = set(connection.introspection.table_names())

    if cat_table not in tables:
        schema_editor.create_model(Category)

    video_columns = _video_column_names(schema_editor)

    if "category_id" not in video_columns:
        field = models.ForeignKey(
            Category,
            on_delete=django.db.models.deletion.PROTECT,
            related_name="videos",
            null=True,
            blank=True,
            verbose_name="Kind",
        )
        field.set_attributes_from_name("category")
        schema_editor.add_field(Video, field)
        video_columns = _video_column_names(schema_editor)

    seed_categories_and_migrate_kind(apps, schema_editor)

    kind_index = "global_solut_kind_dbbbae_idx"
    if "kind" in video_columns and _index_exists(schema_editor, video_table, kind_index):
        schema_editor.remove_index(
            Video,
            models.Index(
                fields=["kind", "is_active", "published_at"],
                name=kind_index,
            ),
        )

    if "kind" in video_columns:
        schema_editor.remove_field(Video, Video._meta.get_field("kind"))
        video_columns = _video_column_names(schema_editor)

    category_field = Video._meta.get_field("category")
    if category_field.null:
        new_field = models.ForeignKey(
            Category,
            on_delete=django.db.models.deletion.PROTECT,
            related_name="videos",
            verbose_name="Kind",
        )
        new_field.set_attributes_from_name("category")
        schema_editor.alter_field(Video, category_field, new_field)

    new_index = "gs_video_cat_pub_idx"
    if not _index_exists(schema_editor, video_table, new_index):
        schema_editor.add_index(
            Video,
            models.Index(
                fields=["category", "is_active", "published_at"],
                name=new_index,
            ),
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("global_solutions", "0003_globalsolutionspage_and_index_fields"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(apply_videocategory_schema, noop_reverse),
            ],
            state_operations=[
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
            ],
        ),
    ]
