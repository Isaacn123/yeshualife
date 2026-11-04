"""Staff API URL map for response-page video uploader JS."""

from __future__ import annotations

from uuid import UUID

from django.urls import reverse


def response_video_api_urls_for(video_id: UUID | str) -> dict[str, str]:
    vid = video_id if isinstance(video_id, UUID) else UUID(str(video_id))
    return {
        "meta": reverse("karamoja_response:update_video_meta", kwargs={"video_id": vid}),
        "b2_create": reverse("karamoja_response:b2_create_multipart", kwargs={"video_id": vid}),
        "b2_part_url": reverse("karamoja_response:b2_part_url", kwargs={"video_id": vid}),
        "b2_complete": reverse("karamoja_response:b2_complete_multipart", kwargs={"video_id": vid}),
        "thumbnails": reverse("karamoja_response:video_thumbnails", kwargs={"video_id": vid}),
        "thumbnails_generate": reverse(
            "karamoja_response:video_thumbnails_generate", kwargs={"video_id": vid}
        ),
        "thumbnails_select": reverse(
            "karamoja_response:video_thumbnail_select", kwargs={"video_id": vid}
        ),
        "thumbnails_upload": reverse(
            "karamoja_response:video_thumbnail_upload", kwargs={"video_id": vid}
        ),
        "delete": reverse("karamoja_response:delete_video", kwargs={"video_id": vid}),
    }
