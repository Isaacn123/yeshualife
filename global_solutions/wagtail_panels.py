"""Wagtail admin panels for Global Solutions."""

from __future__ import annotations

import json

from wagtail.admin.panels import Panel

from .api_urls import video_api_urls_for


class GlobalSolutionsVideoB2UploadPanel(Panel):
    """
    Embeds the direct-to-B2 multipart uploader on the Global Solutions video snippet.
    The video row must be saved once (draft) so a UUID exists before upload.
    """

    class BoundPanel(Panel.BoundPanel):
        template_name = "global_solutions/wagtail_panels/video_b2_upload.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            pk = getattr(self.instance, "pk", None)
            vid = str(pk) if pk else ""
            context["video_id"] = vid
            if pk:
                context["gs_video_api_urls"] = video_api_urls_for(pk)
                context["has_uploaded_source"] = bool((getattr(self.instance, "original_b2_key", "") or "").strip())
            return context


class GlobalSolutionsSimilarVideosPanel(Panel):
    """
    Optional extra clips on the same snippet edit page (upload + thumbnail per clip).
    Only available after the main video row is saved.
    """

    class BoundPanel(Panel.BoundPanel):
        template_name = "global_solutions/wagtail_panels/similar_videos_panel.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            instance = self.instance
            pk = getattr(instance, "pk", None)
            context["video_id"] = str(pk) if pk else ""
            context["can_manage_similar"] = bool(
                pk and not getattr(instance, "parent_video_id", None)
            )
            if context["can_manage_similar"]:
                from django.urls import reverse

                blocks = []
                for sv in instance.similar_videos.all().order_by("sort_order", "created_at"):
                    blocks.append(
                        {
                            "similar": sv,
                            "api_urls_json": json.dumps(video_api_urls_for(sv.pk)),
                        }
                    )
                context["similar_video_blocks"] = blocks
                context["similar_create_url"] = reverse(
                    "global_solutions:create_similar_video",
                    kwargs={"video_id": pk},
                )
            else:
                context["similar_video_blocks"] = []
            return context
