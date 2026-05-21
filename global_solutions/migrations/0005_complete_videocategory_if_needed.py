# Finish 0004 on production if the category table was created but 0004 did not complete.
# Safe to run on a DB that already finished 0004 (no-op).

from django.db import migrations, models
import django.db.models.deletion


def _video_column_names(schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(
            cursor, "global_solutions_globalsolutionsvideo"
        )
    return {col.name for col in description}


def _index_exists(schema_editor, table, index_name):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        constraints = connection.introspection.get_constraints(cursor, table)
    return index_name in constraints


def complete_videocategory(apps, schema_editor):
    Category = apps.get_model("global_solutions", "GlobalSolutionsVideoCategory")
    Video = apps.get_model("global_solutions", "GlobalSolutionsVideo")
    video_table = Video._meta.db_table
    video_columns = _video_column_names(schema_editor)

    defaults = [
        ("feeding", "Feeding", "{count} clips", "right", 10),
        ("preaching", "Preachings", "{count} clips", "left", 20),
        ("learning", "Learning", "{count} clips", "right", 30),
    ]
    by_slug = {}
    for slug, name, heading, align, order in defaults:
        cat, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "heading_upper": heading,
                "title_align": align,
                "sort_order": order,
                "is_active": True,
            },
        )
        by_slug[slug] = cat

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

    if "kind" in video_columns:
        for video in Video.objects.all():
            old_kind = getattr(video, "kind", None) or ""
            cat = by_slug.get(old_kind)
            if cat and not video.category_id:
                video.category_id = cat.pk
                video.save(update_fields=["category_id"])

        kind_index = "global_solut_kind_dbbbae_idx"
        if _index_exists(schema_editor, video_table, kind_index):
            schema_editor.remove_index(
                Video,
                models.Index(
                    fields=["kind", "is_active", "published_at"],
                    name=kind_index,
                ),
            )
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
        ("global_solutions", "0004_videocategory_and_fk"),
    ]

    operations = [
        migrations.RunPython(complete_videocategory, noop_reverse),
    ]
