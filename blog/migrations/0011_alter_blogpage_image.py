# Generated by Django 4.2.7 on 2023-11-28 17:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0025_alter_image_file_alter_rendition_file'),
        ('blog', '0010_alter_blogpage_body_content'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blogpage',
            name='image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailimages.image'),
        ),
    ]
