from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("global_solutions", "0006_globalsolutionsvideo_likes"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalsolutionsvideo",
            name="poster_b2_key",
            field=models.CharField(
                blank=True,
                default="",
                help_text="B2 object key for the selected thumbnail (resolved to a readable URL on display).",
                max_length=512,
            ),
        ),
    ]
