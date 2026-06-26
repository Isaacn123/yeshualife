"""Print thumbnail URL for a video and verify the B2 object exists."""

from django.core.management.base import BaseCommand

from global_solutions.b2 import b2_head_object, b2_public_url
from global_solutions.models import GlobalSolutionsVideo
from global_solutions.thumbnails import poster_url_for_key


class Command(BaseCommand):
    help = "Diagnose Global Solutions poster/thumbnail URLs for one video."

    def add_arguments(self, parser):
        parser.add_argument("--video-id", required=True, help="GlobalSolutionsVideo UUID")
        parser.add_argument(
            "--key",
            help="Optional B2 key to test instead of the video's poster_b2_key",
        )

    def handle(self, *args, **options):
        video = GlobalSolutionsVideo.objects.filter(pk=options["video_id"]).first()
        if not video:
            self.stderr.write("Video not found.")
            return

        key = (options.get("key") or video.poster_b2_key or "").strip()
        if not key:
            self.stderr.write("No poster_b2_key on this video. Generate thumbnails first.")
            return

        public_url = b2_public_url(key)
        display_url = poster_url_for_key(key)

        self.stdout.write(f"Video: {video.title} ({video.id})")
        self.stdout.write(f"Category slug: {video.storage_path_slug}")
        self.stdout.write(f"B2 key: {key}")
        self.stdout.write(f"Public URL: {public_url}")
        self.stdout.write(f"App thumbnail URL: {display_url}")

        try:
            meta = b2_head_object(key)
            size = meta.get("ContentLength", "?")
            ctype = meta.get("ContentType", "?")
            self.stdout.write(self.style.SUCCESS(f"B2 object exists ({size} bytes, {ctype})"))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"B2 object missing or inaccessible: {exc}"))
            self.stderr.write("Re-run “Generate 3 options” in Wagtail to recreate poster files.")

        self.stdout.write("\nTest in browser or curl:")
        self.stdout.write(f"  curl -I \"{public_url}\"")
