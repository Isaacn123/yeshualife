import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("global_solutions", "0010_home_card_link_global_solutions_url"),
        ("wagtailimages", "0025_alter_image_file_alter_rendition_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalsolutionssettings",
            name="hero_image",
            field=models.ForeignKey(
                blank=True,
                help_text="Upload a hero image for the Global Solutions hub (recommended).",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="wagtailimages.image",
            ),
        ),
        migrations.AlterField(
            model_name="globalsolutionssettings",
            name="hero_image_url",
            field=models.URLField(
                blank=True,
                default="",
                help_text="Optional legacy fallback URL if you do not upload an image above.",
            ),
        ),
        migrations.AlterField(
            model_name="globalsolutionssettings",
            name="home_card_image",
            field=models.ForeignKey(
                blank=True,
                help_text="Upload a wide background image (1920×1080 recommended) for the main site homepage card.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="wagtailimages.image",
            ),
        ),
    ]
