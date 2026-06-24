from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("global_solutions", "0005_solution_categories"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalsolutionsvideo",
            name="likes",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
