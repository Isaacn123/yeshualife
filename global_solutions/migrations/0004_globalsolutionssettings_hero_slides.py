# Generated manually for Global Solutions hero carousel.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("global_solutions", "0003_globalsolutionspage_and_index_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalsolutionssettings",
            name="hero_image_url_2",
            field=models.URLField(blank=True, default="", help_text="Optional second slide."),
        ),
        migrations.AddField(
            model_name="globalsolutionssettings",
            name="hero_image_url_3",
            field=models.URLField(blank=True, default="", help_text="Optional third slide."),
        ),
    ]
