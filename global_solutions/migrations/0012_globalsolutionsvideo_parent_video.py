from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("global_solutions", "0011_globalsolutionssettings_hero_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalsolutionsvideo",
            name="parent_video",
            field=models.ForeignKey(
                blank=True,
                help_text="When set, this clip is an optional extra video shown on the main video's detail page (not listed separately on the hub).",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="similar_videos",
                to="global_solutions.globalsolutionsvideo",
            ),
        ),
        migrations.AddIndex(
            model_name="globalsolutionsvideo",
            index=models.Index(fields=["parent_video", "sort_order"], name="gs_video_parent_sort_idx"),
        ),
    ]
