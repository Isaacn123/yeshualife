from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("global_solutions", "0012_globalsolutionsvideo_parent_video"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalsolutionsvideo",
            name="shares",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
