import django.db.models.deletion
import modelcluster.fields
import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("wagtailcore", "0089_log_entry_data_json_null_to_object"),
        ("wagtailimages", "0025_alter_image_file_alter_rendition_file"),
    ]

    operations = [
        migrations.CreateModel(
            name="AboutPage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.page",
                    ),
                ),
                (
                    "organization_name",
                    models.CharField(
                        default="Yeshua Life Limited",
                        help_text="Small line above the page title.",
                        max_length=120,
                    ),
                ),
                (
                    "lead",
                    models.TextField(help_text="Short introduction under the title."),
                ),
                (
                    "image_alt",
                    models.CharField(
                        blank=True,
                        default="Agricultural work supported by Yeshua Life in Karamoja",
                        max_length=200,
                    ),
                ),
                (
                    "image_caption",
                    models.CharField(
                        blank=True, default="Karamoja, Uganda", max_length=200
                    ),
                ),
                (
                    "organization_heading",
                    models.CharField(default="The organization", max_length=80),
                ),
                ("body", wagtail.fields.RichTextField()),
                ("work_heading", models.CharField(default="Areas of work", max_length=80)),
                ("office_heading", models.CharField(default="Office", max_length=80)),
                ("address", models.TextField(help_text="Line breaks are kept.")),
                ("phone", models.CharField(blank=True, max_length=40)),
                ("email", models.EmailField(blank=True, max_length=254)),
                (
                    "primary_label",
                    models.CharField(blank=True, default="Contact", max_length=40),
                ),
                (
                    "primary_url",
                    models.CharField(
                        blank=True,
                        default="/contact/",
                        help_text="Path on this site, such as /contact/",
                        max_length=200,
                    ),
                ),
                (
                    "secondary_label",
                    models.CharField(blank=True, default="Pay online", max_length=40),
                ),
                (
                    "secondary_url",
                    models.CharField(blank=True, default="/payments", max_length=200),
                ),
                (
                    "hero_image",
                    models.ForeignKey(
                        blank=True,
                        help_text="Leave empty to keep the current Karamoja photograph.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="wagtailimages.image",
                    ),
                ),
            ],
            options={
                "verbose_name": "About page",
            },
            bases=("wagtailcore.page",),
        ),
        migrations.CreateModel(
            name="AboutWorkArea",
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
                ("sort_order", models.IntegerField(blank=True, editable=False, null=True)),
                ("title", models.CharField(max_length=80)),
                ("summary", models.TextField()),
                (
                    "url",
                    models.CharField(
                        blank=True,
                        help_text="Path on this site, such as /karamoja. Leave empty for a line with no link.",
                        max_length=200,
                    ),
                ),
                (
                    "page",
                    modelcluster.fields.ParentalKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="work_areas",
                        to="about.aboutpage",
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order"],
                "abstract": False,
            },
        ),
    ]
