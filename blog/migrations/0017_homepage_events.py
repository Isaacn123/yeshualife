from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailimages", "0025_alter_image_file_alter_rendition_file"),
        ("blog", "0016_blogindexpage_image"),
    ]

    operations = [
        migrations.CreateModel(
            name="HomepageEventsSettings",
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
                (
                    "section_enabled",
                    models.BooleanField(
                        default=False,
                        help_text="Show the events section on the main homepage.",
                    ),
                ),
                (
                    "section_eyebrow",
                    models.CharField(
                        blank=True, default="What's next", max_length=80
                    ),
                ),
                (
                    "section_title",
                    models.CharField(
                        default="Upcoming events & announcements", max_length=160
                    ),
                ),
                (
                    "section_lead",
                    models.TextField(
                        blank=True,
                        default=(
                            "Join us in the field, online, and in community — "
                            "dates and highlights worth marking on your calendar."
                        ),
                    ),
                ),
                (
                    "max_items",
                    models.PositiveSmallIntegerField(
                        default=3,
                        help_text=(
                            "Maximum number of cards to show "
                            "(newest / highest priority first)."
                        ),
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Homepage events settings",
                "verbose_name_plural": "Homepage events settings",
            },
        ),
        migrations.CreateModel(
            name="HomepageEvent",
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
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Uncheck to hide this item without deleting it.",
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("event", "Event"),
                            ("announcement", "Announcement"),
                            ("promo", "Promo"),
                        ],
                        default="event",
                        max_length=20,
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                (
                    "event_date",
                    models.DateField(
                        blank=True,
                        help_text="Optional. Shown at the top of the card, e.g. August 29.",
                        null=True,
                    ),
                ),
                (
                    "event_time_label",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text='Optional time text, e.g. "6:00 pm" or "All day".',
                        max_length=80,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Short paragraph (1–3 sentences).",
                    ),
                ),
                (
                    "link",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Where the button goes. Leave blank to hide the button.",
                        max_length=300,
                    ),
                ),
                (
                    "button_text",
                    models.CharField(blank=True, default="Learn more", max_length=80),
                ),
                (
                    "starts_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Optional. Card stays hidden until this date/time.",
                        null=True,
                    ),
                ),
                (
                    "ends_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Optional. Card is hidden after this date/time.",
                        null=True,
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0, help_text="Lower numbers appear first."
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "image",
                    models.ForeignKey(
                        blank=True,
                        help_text="Optional card image (640×360 or wider recommended).",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="wagtailimages.image",
                    ),
                ),
            ],
            options={
                "verbose_name": "Homepage event / announcement",
                "verbose_name_plural": "Homepage events & announcements",
                "ordering": ["sort_order", "event_date", "-created_at"],
            },
        ),
    ]
