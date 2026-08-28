from django.db import migrations, models
from django.utils.text import slugify


def populate_event_slugs(apps, schema_editor):
    HomepageEvent = apps.get_model("blog", "HomepageEvent")
    used: set[str] = set()
    for event in HomepageEvent.objects.order_by("pk"):
        base = slugify(event.title)[:200] or "event"
        slug = base
        n = 2
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        used.add(slug)
        event.slug = slug
        event.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0018_homepageevent_video"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepageevent",
            name="slug",
            field=models.SlugField(
                blank=True,
                help_text="URL for the public event page (used when sharing). Auto-filled from title if left blank.",
                max_length=220,
                null=True,
            ),
        ),
        migrations.RunPython(populate_event_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="homepageevent",
            name="slug",
            field=models.SlugField(
                blank=True,
                help_text="URL for the public event page (used when sharing). Auto-filled from title if left blank.",
                max_length=220,
                unique=True,
            ),
        ),
    ]
