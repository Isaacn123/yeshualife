"""Wagtail admin panel for response-page videos."""

from __future__ import annotations

import json

from django.urls import reverse
from wagtail.admin.panels import Panel

from .api_urls import response_video_api_urls_for


class ResponsePageVideosPanel(Panel):
    """Upload and manage videos on a Karamoja Response page (same B2 flow as Global Solutions)."""

    class BoundPanel(Panel.BoundPanel):
        template_name = "karamoja_response/wagtail_panels/response_videos_panel.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            page = self.instance
            pk = getattr(page, "pk", None)
            context["page_id"] = pk
            context["can_manage_videos"] = bool(pk)
            blocks = []
            if pk:
                context["create_video_url"] = reverse(
                    "karamoja_response:create_video",
                    kwargs={"page_id": pk},
                )
                for video in page.response_videos.all().order_by("sort_order", "created_at"):
                    blocks.append(
                        {
                            "video": video,
                            "api_urls_json": json.dumps(response_video_api_urls_for(video.pk)),
                        }
                    )
            context["video_blocks"] = blocks
            return context
