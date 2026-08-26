from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("global_solutions", "0013_globalsolutionsvideo_shares"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalsolutionsvideo",
            name="page_views",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Visits to the video detail page (not embed plays).",
            ),
        ),
    ]
