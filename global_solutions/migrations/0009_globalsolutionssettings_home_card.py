import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("global_solutions", "0008_solutioncategory_show_on_home_help_text"),
        ("wagtailimages", "0025_alter_image_file_alter_rendition_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalsolutionssettings",
            name="home_card_button_text",
            field=models.CharField(blank=True, default="Explore Global Solutions", max_length=80),
        ),
        migrations.AddField(
            model_name="globalsolutionssettings",
            name="home_card_description",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="globalsolutionssettings",
            name="home_card_enabled",
            field=models.BooleanField(
                default=True,
                help_text="Show a Global Solutions card on the main site homepage.",
            ),
        ),
        migrations.AddField(
            model_name="globalsolutionssettings",
            name="home_card_image",
            field=models.ForeignKey(
                blank=True,
                help_text="Background image for the homepage card.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="wagtailimages.image",
            ),
        ),
        migrations.AddField(
            model_name="globalsolutionssettings",
            name="home_card_link",
            field=models.CharField(blank=True, default="/farmhub/", max_length=300),
        ),
        migrations.AddField(
            model_name="globalsolutionssettings",
            name="home_card_title",
            field=models.CharField(blank=True, default="Global Solutions", max_length=160),
        ),
    ]
