# Merge parallel 0004 migration branches (no database changes).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("global_solutions", "0004_merge_branches"),
        ("global_solutions", "0004_videocategory_and_fk"),
    ]

    operations = []
