"""Diagnose B2 playback for a Global Solutions video."""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from botocore.exceptions import ClientError

from global_solutions.b2 import b2_head_object, b2_presigned_get_url, get_b2_config
from global_solutions.models import GlobalSolutionsVideo


class Command(BaseCommand):
    help = "Check B2 object + playback URL for a video (by UUID or slug)."

    def add_arguments(self, parser):
        parser.add_argument("id_or_slug", help="Video UUID or slug")
        parser.add_argument(
            "--curl",
            action="store_true",
            help="Print a curl command to test the presigned URL from the server",
        )

    def handle(self, *args, **options):
        ref = (options["id_or_slug"] or "").strip()
        video = GlobalSolutionsVideo.objects.filter(slug=ref).first()
        if not video:
            video = GlobalSolutionsVideo.objects.filter(pk=ref).first()
        if not video:
            raise CommandError(f"No video found for {ref!r}")

        self.stdout.write(f"Title: {video.title}")
        self.stdout.write(f"Slug: {video.slug}")
        self.stdout.write(f"Status: {video.status}  active={video.is_active}")
        self.stdout.write(f"B2 key: {video.original_b2_key or '(empty)'}")
        self.stdout.write(f"Content-Type (DB): {video.original_content_type or '(empty)'}")
        self.stdout.write(f"Size bytes (DB): {video.original_size_bytes or '(unknown)'}")

        if not video.original_b2_key:
            raise CommandError("Video has no original_b2_key — re-upload required.")

        cfg = get_b2_config()
        self.stdout.write(f"Bucket: {cfg.bucket_name}")
        self.stdout.write(f"S3 endpoint: {cfg.endpoint_url}")

        try:
            head = b2_head_object(video.original_b2_key)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "unknown")
            self.stderr.write(self.style.ERROR(f"B2 HeadObject failed: {code}"))
            self.stderr.write(
                "The key in the database does not match an object in the bucket. "
                "Check the exact filename (spaces/casing) in B2 vs original_b2_key."
            )
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("B2 object exists."))
        self.stdout.write(f"B2 Content-Type: {head.get('ContentType', '(none)')}")
        self.stdout.write(f"B2 Content-Length: {head.get('ContentLength', '(none)')}")
        self.stdout.write(f"B2 Accept-Ranges: {head.get('AcceptRanges', '(none)')}")

        content_type = (video.original_content_type or head.get("ContentType") or "video/mp4").strip()
        url = b2_presigned_get_url(
            video.original_b2_key,
            response_content_type=content_type,
        )
        self.stdout.write(f"\nPresigned playback URL (24h):\n{url}\n")

        if options["curl"]:
            self.stdout.write("Test from server:\n")
            self.stdout.write(f'  curl -I "{url}"\n')

        self.stdout.write(
            "\nIf the object exists but the browser will not play:\n"
            "  1. B2 bucket CORS must allow https://yeshualifeug.com (and Range requests).\n"
            "  2. MP4 should be H.264 + AAC ('fast start' / web optimized).\n"
            "  3. Filenames with spaces work but re-upload with a simple name is safer.\n"
        )
