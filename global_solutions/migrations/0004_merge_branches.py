# Empty merge node if this branch was created locally before 0004_videocategory_and_fk.
# Safe no-op when already applied; 0005_merge ties the graph together.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("global_solutions", "0003_globalsolutionspage_and_index_fields"),
    ]

    operations = []
