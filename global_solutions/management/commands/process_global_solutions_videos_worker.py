from __future__ import annotations

import time

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Continuously processes Global Solutions videos marked PROCESSING (for systemd/worker usage)."

    def add_arguments(self, parser):
        parser.add_argument("--interval-seconds", type=int, default=20)
        parser.add_argument("--limit", type=int, default=1)

    def handle(self, *args, **options):
        interval = max(3, int(options["interval_seconds"]))
        limit = max(1, int(options["limit"]))

        self.stdout.write(
            self.style.SUCCESS(
                f"Global Solutions video worker started (interval={interval}s, limit={limit})."
            )
        )

        while True:
            try:
                call_command("process_global_solutions_videos", limit=limit)
            except Exception as e:
                # Keep running; surface error in logs.
                self.stderr.write(f"Worker error: {e}")
            time.sleep(interval)

