# Compatibility NO-OP migration.
#
# Some environments contain this migration file and depend on it.
# The `LandClearingIndexPage.image` field is already present in 0001_initial
# in this codebase, so this migration does not need to change schema/state.

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("landClearing", "0002_rename_awardspagegalleryimage_landclearingpagegalleryimage"),
    ]

    operations = [
        migrations.RunPython(migrations.RunPython.noop, migrations.RunPython.noop),
    ]

