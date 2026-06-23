"""
Upload files from the local media/ directory into the configured default storage (R2).

Run once after enabling USE_R2_MEDIA on production:

    python manage.py sync_local_media_to_r2
"""

from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Copy existing files from MEDIA_ROOT into Cloudflare R2 (default storage)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List files that would be uploaded without uploading.",
        )

    def handle(self, *args, **options):
        if not getattr(settings, "USE_R2_MEDIA", False):
            raise CommandError("USE_R2_MEDIA is not enabled; configure R2 in .env first.")

        media_root = Path(settings.MEDIA_ROOT)
        if not media_root.is_dir():
            raise CommandError(f"MEDIA_ROOT does not exist: {media_root}")

        uploaded = 0
        skipped = 0

        for path in sorted(media_root.rglob("*")):
            if not path.is_file():
                continue

            key = path.relative_to(media_root).as_posix()
            if default_storage.exists(key):
                skipped += 1
                self.stdout.write(f"skip (exists): {key}")
                continue

            if options["dry_run"]:
                self.stdout.write(f"would upload: {key}")
                uploaded += 1
                continue

            with path.open("rb") as source:
                default_storage.save(key, source)
            uploaded += 1
            self.stdout.write(f"uploaded: {key}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. uploaded={uploaded} skipped={skipped} dry_run={options['dry_run']}"
            )
        )
