from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("wagtaildocs", "0012_uploadeddocument"),
        ("blog", "0017_homepage_events"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepageevent",
            name="video",
            field=models.ForeignKey(
                blank=True,
                help_text="Optional MP4 or WebM clip shown below the description on the card.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="wagtaildocs.document",
            ),
        ),
    ]
