# Generated by Django 4.2.7 on 2024-08-29 18:59

from django.db import migrations
import wagtail.blocks
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('awards', '0003_awardsindexpage_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='awardspage',
            name='body',
            field=wagtail.fields.StreamField([('heading', wagtail.blocks.CharBlock(form_classname='title')), ('paragraph', wagtail.blocks.RichTextBlock()), ('image', wagtail.blocks.ChooserBlock()), ('video', wagtail.blocks.EmailBlock())], use_json_field=True),
        ),
    ]
