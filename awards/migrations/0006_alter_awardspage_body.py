# Generated by Django 4.2.7 on 2025-05-09 23:51

from django.db import migrations
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('awards', '0005_alter_awardspage_body'),
    ]

    operations = [
        migrations.AlterField(
            model_name='awardspage',
            name='body',
            field=wagtail.fields.RichTextField(blank=True, null=True),
        ),
    ]
