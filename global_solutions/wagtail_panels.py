"""Wagtail admin panels for Global Solutions."""

from __future__ import annotations

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
            return context
