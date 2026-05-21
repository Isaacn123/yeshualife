# Revert dynamic video categories: restore hardcoded kind column, drop category table.
# DB-only fix; Django state should already match 0003 (kind) after removing bad migration rows.

from django.db import migrations, models


def _video_columns(schema_editor):
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


def restore_video_kind(apps, schema_editor):
    connection = schema_editor.connection
    tables = set(connection.introspection.table_names())
    video_table = "global_solutions_globalsolutionsvideo"
    cat_table = "global_solutions_globalsolutionsvideocategory"
    q = schema_editor.quote_name
    video_columns = _video_columns(schema_editor)

    if "kind" not in video_columns:
        schema_editor.execute(
            f"ALTER TABLE {q(video_table)} ADD COLUMN kind varchar(16) NULL"
        )
        video_columns = _video_columns(schema_editor)

    if "category_id" in video_columns and cat_table in tables:
        schema_editor.execute(
            f"UPDATE {q(video_table)} v "
            f"INNER JOIN {q(cat_table)} c ON v.category_id = c.id "
            f"SET v.kind = c.slug "
            f"WHERE v.kind IS NULL OR v.kind = ''"
        )
        schema_editor.execute(
            f"UPDATE {q(video_table)} SET kind = 'feeding' "
            f"WHERE kind IS NULL OR kind = ''"
        )

    if _index_exists(schema_editor, video_table, "gs_video_cat_pub_idx"):
        schema_editor.execute(
            f"ALTER TABLE {q(video_table)} DROP INDEX {q('gs_video_cat_pub_idx')}"
        )

    if "category_id" in video_columns:
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, video_table)
        for name, info in constraints.items():
            cols = info.get("columns") or []
            if info.get("foreign_key") and "category_id" in cols:
                schema_editor.execute(
                    f"ALTER TABLE {q(video_table)} DROP FOREIGN KEY {q(name)}"
                )
        schema_editor.execute(
            f"ALTER TABLE {q(video_table)} DROP COLUMN category_id"
        )

    if cat_table in tables:
        schema_editor.execute(f"DROP TABLE {q(cat_table)}")

    schema_editor.execute(
        f"ALTER TABLE {q(video_table)} MODIFY COLUMN kind varchar(16) NOT NULL"
    )

    if not _index_exists(schema_editor, video_table, "global_solut_kind_dbbbae_idx"):
        Video = apps.get_model("global_solutions", "GlobalSolutionsVideo")
        schema_editor.add_index(
            Video,
            models.Index(
                fields=["kind", "is_active", "published_at"],
                name="global_solut_kind_dbbbae_idx",
            ),
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    # MySQL cannot roll back DDL; raw ALTER TABLE must run outside a transaction.
    atomic = False

    dependencies = [
        ("global_solutions", "0003_globalsolutionspage_and_index_fields"),
    ]

    operations = [
        migrations.RunPython(restore_video_kind, noop_reverse),
    ]
