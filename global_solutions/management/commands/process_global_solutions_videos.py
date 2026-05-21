from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from global_solutions.b2 import b2_public_url, get_b2_config, get_b2_s3_client
from global_solutions.models import GlobalSolutionsVideo, GlobalSolutionsVideoStatus


def _ffmpeg_bin() -> str:
    return os.environ.get("FFMPEG_BIN", "ffmpeg")


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            + " ".join(cmd)
            + "\n\nstdout:\n"
            + (proc.stdout or "")
            + "\n\nstderr:\n"
            + (proc.stderr or "")
        )


class Command(BaseCommand):
    help = "Transcode Global Solutions videos (PROCESSING) to HLS and upload to B2."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=3)
        parser.add_argument("--video-id", type=str, default="")

    def handle(self, *args, **options):
        limit = options["limit"]
        video_id = (options.get("video_id") or "").strip()

        qs = GlobalSolutionsVideo.objects.filter(status=GlobalSolutionsVideoStatus.PROCESSING)
        if video_id:
            qs = qs.filter(id=video_id)

        videos = list(qs.order_by("updated_at")[:limit])
        if not videos:
            self.stdout.write("No videos to process.")
            return

        s3 = get_b2_s3_client()
        cfg = get_b2_config()

        for v in videos:
            if not v.original_b2_key:
                v.status = GlobalSolutionsVideoStatus.FAILED
                v.last_error = "Missing original_b2_key"
                v.save(update_fields=["status", "last_error", "updated_at"])
                continue

            try:
                self.stdout.write(f"Processing {v.id} ({v.title})")

                input_url = s3.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": cfg.bucket_name, "Key": v.original_b2_key},
                    ExpiresIn=60 * 60,
                )

                with tempfile.TemporaryDirectory(prefix="gs_hls_") as tmpdir:
                    out_dir = Path(tmpdir) / "hls"
                    out_dir.mkdir(parents=True, exist_ok=True)

                    # Single-variant HLS (720p-ish) for a strong baseline.
                    # You can extend to multi-bitrate later.
                    master = out_dir / "master.m3u8"
                    variant = out_dir / "v0.m3u8"
                    seg_pattern = str(out_dir / "seg_%05d.ts")

                    cmd = [
                        _ffmpeg_bin(),
                        "-y",
                        "-i",
                        input_url,
                        "-vf",
                        "scale='min(1280,iw)':-2",
                        "-c:v",
                        "libx264",
                        "-preset",
                        "veryfast",
                        "-crf",
                        "23",
                        "-c:a",
                        "aac",
                        "-b:a",
                        "128k",
                        "-hls_time",
                        "4",
                        "-hls_playlist_type",
                        "vod",
                        "-hls_segment_filename",
                        seg_pattern,
                        str(variant),
                    ]
                    _run(cmd)

                    # Create a simple HLS master playlist referencing the variant.
                    master_contents = "\n".join(
                        [
                            "#EXTM3U",
                            "#EXT-X-VERSION:3",
                            "#EXT-X-STREAM-INF:BANDWIDTH=2200000,RESOLUTION=1280x720,CODECS=\"avc1.64001f,mp4a.40.2\"",
                            variant.name,
                            "",
                        ]
                    )
                    master.write_text(master_contents, encoding="utf-8")

                    # Upload all HLS outputs to B2
                    base_key = f"global-solutions/hls/{v.kind}/{v.id}"
                    for p in out_dir.iterdir():
                        if p.is_dir():
                            continue
                        key = f"{base_key}/{p.name}"
                        extra_args = {}
                        if p.suffix == ".m3u8":
                            extra_args["ContentType"] = "application/vnd.apple.mpegurl"
                        elif p.suffix == ".ts":
                            extra_args["ContentType"] = "video/mp2t"
                        s3.upload_file(str(p), cfg.bucket_name, key, ExtraArgs=extra_args or None)

                    v.hls_master_manifest_key = f"{base_key}/{master.name}"
                    v.hls_master_manifest_url = b2_public_url(v.hls_master_manifest_key)
                    v.status = GlobalSolutionsVideoStatus.READY
                    v.last_error = ""
                    v.save(
                        update_fields=[
                            "hls_master_manifest_key",
                            "hls_master_manifest_url",
                            "status",
                            "last_error",
                            "updated_at",
                        ]
                    )

            except Exception as e:
                v.status = GlobalSolutionsVideoStatus.FAILED
                v.last_error = str(e)
                v.save(update_fields=["status", "last_error", "updated_at"])
                self.stderr.write(f"Failed {v.id}: {e}")

