from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailimages", "0025_alter_image_file_alter_rendition_file"),
        ("landClearing", "0001_initial"),
    ]

    operations = [
        # NOTE:
        # This migration was generated with an invalid RenameModel reference:
        # `AwardsPageGalleryImage` is not a model in the `landClearing` app state,
        # which causes a KeyError during `migrate`.
        #
        # Kept as a no-op (commented out) so later migrations can run.
        #
        # migrations.RenameModel(
        #     old_name="AwardsPageGalleryImage",
        #     new_name="LandClearingPageGalleryImage",
        # ),
    ]

