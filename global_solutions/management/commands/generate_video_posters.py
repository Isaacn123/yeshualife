from __future__ import annotations

from django.core.management.base import BaseCommand

from global_solutions.models import GlobalSolutionsVideo, GlobalSolutionsVideoStatus
from global_solutions.thumbnails import FFmpegNotFoundError, ensure_ffmpeg_available, generate_poster_for_video


class Command(BaseCommand):
    help = "Generate poster thumbnails for Global Solutions videos missing poster_image_url."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)
        parser.add_argument("--video-id", type=str, default="")
        parser.add_argument("--force", action="store_true", help="Regenerate even if poster exists")

    def handle(self, *args, **options):
        try:
            ffmpeg_path = ensure_ffmpeg_available()
            self.stdout.write(f"Using ffmpeg: {ffmpeg_path}")
        except FFmpegNotFoundError as e:
            self.stderr.write(self.style.ERROR(str(e)))
            return

        limit = options["limit"]
        video_id = (options.get("video_id") or "").strip()
        force = options["force"]

        qs = GlobalSolutionsVideo.objects.filter(status=GlobalSolutionsVideoStatus.READY)
        if not force:
            qs = qs.filter(poster_image_url="")
        if video_id:
            qs = qs.filter(id=video_id)

        videos = list(qs.order_by("-published_at")[:limit])
        if not videos:
            self.stdout.write("No videos need poster generation.")
            return

        ok = fail = 0
        for video in videos:
            self.stdout.write(f"Poster: {video.id} — {video.title}")
            try:
                if generate_poster_for_video(video):
                    ok += 1
                    self.stdout.write(self.style.SUCCESS("  OK"))
                else:
                    fail += 1
                    self.stdout.write(self.style.WARNING("  Skipped (ffmpeg failed or no source)"))
            except Exception as e:
                fail += 1
                self.stderr.write(f"  Failed: {e}")

        self.stdout.write(self.style.SUCCESS(f"Done. success={ok} failed={fail}"))
