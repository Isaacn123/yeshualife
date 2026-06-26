from __future__ import annotations

from django.core.management.base import BaseCommand

from global_solutions.thumbnails import FFmpegNotFoundError, ffmpeg_diagnostic, ensure_ffmpeg_available


class Command(BaseCommand):
    help = "Show which ffmpeg binary Django will use for video thumbnails."

    def handle(self, *args, **options):
        diag = ffmpeg_diagnostic()
        self.stdout.write("FFmpeg diagnostic:")
        for key, value in diag.items():
            self.stdout.write(f"  {key}: {value}")
        try:
            path = ensure_ffmpeg_available()
            self.stdout.write(self.style.SUCCESS(f"\nOK — resolved ffmpeg: {path}"))
        except FFmpegNotFoundError as exc:
            self.stderr.write(self.style.ERROR(f"\nNOT FOUND — {exc}"))
            self.stderr.write(
                "\nInstall in the SAME venv gunicorn uses, e.g.:\n"
                "  source /var/www/yeshualife/venv/bin/activate\n"
                "  pip install imageio-ffmpeg\n"
                "Or: sudo apt install -y ffmpeg\n"
            )
