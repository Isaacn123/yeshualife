"""Canonical URL reversing for Global Solutions video staff APIs (used by uploader JS)."""

from __future__ import annotations

import uuid
from uuid import UUID

from django.urls import reverse

# Placeholder UUID for building URL templates (standalone uploader); replaced in JS per video.
_VIDEO_API_PLACEHOLDER = uuid.UUID("00000000-0000-0000-0000-000000000000")


def video_api_urls_for(video_id: UUID | str) -> dict[str, str]:
    """Return URL paths for staff video APIs (respects FORCE_SCRIPT_NAME / subpath installs)."""
    vid = video_id if isinstance(video_id, UUID) else UUID(str(video_id))
    return {
        "create": reverse("global_solutions:create_video"),
        "meta": reverse("global_solutions:update_video_meta", kwargs={"video_id": vid}),
        "b2_create": reverse("global_solutions:b2_create_multipart", kwargs={"video_id": vid}),
        "b2_part_url": reverse("global_solutions:b2_part_url", kwargs={"video_id": vid}),
        "b2_complete": reverse("global_solutions:b2_complete_multipart", kwargs={"video_id": vid}),
        "process": reverse("global_solutions:process_start", kwargs={"video_id": vid}),
        "thumbnails": reverse("global_solutions:video_thumbnails", kwargs={"video_id": vid}),
        "thumbnails_generate": reverse("global_solutions:video_thumbnails_generate", kwargs={"video_id": vid}),
        "thumbnails_select": reverse("global_solutions:video_thumbnail_select", kwargs={"video_id": vid}),
        "thumbnails_upload": reverse("global_solutions:video_thumbnail_upload", kwargs={"video_id": vid}),
    }


def video_api_urls_placeholder_map() -> dict[str, str]:
    """URL map for JSON config (standalone uploader). Includes ``_placeholder`` for JS expansion."""
    ph = str(_VIDEO_API_PLACEHOLDER)
    out = video_api_urls_for(_VIDEO_API_PLACEHOLDER)
    out["_placeholder"] = ph
    return out


def video_api_placeholder_string() -> str:
    return str(_VIDEO_API_PLACEHOLDER)
