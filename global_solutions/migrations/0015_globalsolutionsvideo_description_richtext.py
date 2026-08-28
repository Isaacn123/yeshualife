import wagtail.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("global_solutions", "0014_globalsolutionsvideo_page_views"),
    ]

    operations = [
        migrations.AlterField(
            model_name="globalsolutionsvideo",
            name="description",
            field=wagtail.fields.RichTextField(
                blank=True,
                features=[
                    "h2",
                    "h3",
                    "h4",
                    "bold",
                    "italic",
                    "ol",
                    "ul",
                    "hr",
                    "link",
                    "document-link",
                    "image",
                    "embed",
                ],
            ),
        ),
    ]
