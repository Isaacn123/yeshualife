from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Sync model state only (help_text). Index names are pinned in models.Meta so
    Django does not try to rename legacy indexes that may differ on MySQL.
    """

    dependencies = [
        ("global_solutions", "0007_globalsolutionsvideo_poster_b2_key"),
    ]

    operations = [
        migrations.AlterField(
            model_name="solutioncategory",
            name="show_on_home",
            field=models.BooleanField(
                default=True,
                help_text="Show as a carousel row on the FarmHub homepage.",
            ),
        ),
    ]
