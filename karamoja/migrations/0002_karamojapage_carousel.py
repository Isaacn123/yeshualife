# Generated by Django 4.2.7 on 2023-11-23 16:35

from django.db import migrations
import wagtail.blocks
import wagtail.fields
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('karamoja', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='karamojapage',
            name='carousel',
            field=wagtail.fields.StreamField([('carousel_item', wagtail.blocks.StructBlock([('image', wagtail.images.blocks.ImageChooserBlock())]))], blank=True, use_json_field=True),
        ),
    ]
