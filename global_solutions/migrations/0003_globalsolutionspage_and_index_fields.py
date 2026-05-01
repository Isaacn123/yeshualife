# GlobalSolutionsPage + Awards-style fields on GlobalSolutionsIndexPage.

import django.db.models.deletion
import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("global_solutions", "0002_globalsolutionsindexpage"),
        ("wagtailimages", "0025_alter_image_file_alter_rendition_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalsolutionsindexpage",
            name="intro",
            field=models.CharField(default="", max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="globalsolutionsindexpage",
            name="image",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="wagtailimages.image",
            ),
        ),
        migrations.CreateModel(
            name="GlobalSolutionsPage",
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
                ("date", models.DateField(blank=True, null=True, verbose_name="Post date")),
                ("body", wagtail.fields.RichTextField(blank=True, null=True)),
                ("intro", models.CharField(max_length=200)),
                ("caption", models.CharField(blank=True, max_length=250)),
                (
                    "image",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="wagtailimages.image",
                    ),
                ),
            ],
            options={
                "verbose_name": "Global Solutions page",
            },
            bases=("wagtailcore.page",),
        ),
    ]
