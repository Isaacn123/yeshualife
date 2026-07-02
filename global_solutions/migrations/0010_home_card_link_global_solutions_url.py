from django.db import migrations, models


def migrate_home_card_links(apps, schema_editor):
    GlobalSolutionsSettings = apps.get_model("global_solutions", "GlobalSolutionsSettings")
    for row in GlobalSolutionsSettings.objects.all():
        link = (row.home_card_link or "").strip().rstrip("/").lower()
        if link in {"", "/farmhub", "/global_solutions", "/globalsolutions"}:
            row.home_card_link = "/global-solutions/"
            row.save(update_fields=["home_card_link"])


class Migration(migrations.Migration):

    dependencies = [
        ("global_solutions", "0009_globalsolutionssettings_home_card"),
    ]

    operations = [
        migrations.AlterField(
            model_name="globalsolutionssettings",
            name="home_card_link",
            field=models.CharField(blank=True, default="/global-solutions/", max_length=300),
        ),
        migrations.RunPython(migrate_home_card_links, migrations.RunPython.noop),
    ]
