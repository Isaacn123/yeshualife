from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0019_homepageevent_slug"),
        ("wagtaildocs", "0012_uploadeddocument"),
    ]

    operations = [
        migrations.AlterField(
            model_name="homepageevent",
            name="video",
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "Older document upload. Large files sent this way are rejected with an HTML error. "
                    "Use Video upload below — the file goes straight to R2."
                ),
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="wagtaildocs.document",
            ),
        ),
        migrations.CreateModel(
            name="HomepageEventVideo",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(blank=True, default="", max_length=200)),
                ("is_primary", models.BooleanField(default=False)),
                ("r2_key", models.CharField(blank=True, default="", max_length=500)),
                ("pending_key", models.CharField(blank=True, default="", max_length=500)),
                (
                    "content_type",
                    models.CharField(blank=True, default="video/mp4", max_length=120),
                ),
                ("size_bytes", models.BigIntegerField(blank=True, null=True)),
                ("is_ready", models.BooleanField(default=False)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="event_videos",
                        to="blog.homepageevent",
                    ),
                ),
            ],
            options={
                "ordering": ["-is_primary", "sort_order", "pk"],
            },
        ),
    ]
