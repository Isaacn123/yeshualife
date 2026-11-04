from django.urls import path

from . import video_views

app_name = "karamoja_response"

urlpatterns = [
    # Staff: manage videos on a response page
    path(
        "karamoja-response/api/pages/<int:page_id>/videos/create/",
        video_views.create_video,
        name="create_video",
    ),
    path(
        "karamoja-response/api/videos/<uuid:video_id>/delete/",
        video_views.delete_video,
        name="delete_video",
    ),
    path(
        "karamoja-response/api/videos/<uuid:video_id>/meta/",
        video_views.update_video_meta,
        name="update_video_meta",
    ),
    path(
        "karamoja-response/api/videos/<uuid:video_id>/b2/multipart/create/",
        video_views.b2_create_multipart,
        name="b2_create_multipart",
    ),
    path(
        "karamoja-response/api/videos/<uuid:video_id>/b2/multipart/part-url/",
        video_views.b2_part_url,
        name="b2_part_url",
    ),
    path(
        "karamoja-response/api/videos/<uuid:video_id>/b2/multipart/complete/",
        video_views.b2_complete_multipart,
        name="b2_complete_multipart",
    ),
    path(
        "karamoja-response/api/videos/<uuid:video_id>/thumbnails/",
        video_views.video_thumbnails,
        name="video_thumbnails",
    ),
    path(
        "karamoja-response/api/videos/<uuid:video_id>/thumbnails/generate/",
        video_views.video_thumbnails_generate,
        name="video_thumbnails_generate",
    ),
    path(
        "karamoja-response/api/videos/<uuid:video_id>/thumbnails/select/",
        video_views.video_thumbnail_select,
        name="video_thumbnail_select",
    ),
    path(
        "karamoja-response/api/videos/<uuid:video_id>/thumbnails/upload/",
        video_views.video_thumbnail_upload,
        name="video_thumbnail_upload",
    ),
    # Public engagement
    path(
        "karamoja-response/api/videos/<slug:slug>/like/",
        video_views.api_video_like,
        name="api_video_like",
    ),
    path(
        "karamoja-response/api/videos/<slug:slug>/share/",
        video_views.api_video_share,
        name="api_video_share",
    ),
    path(
        "karamoja-response/api/videos/<slug:slug>/view/",
        video_views.api_video_view,
        name="api_video_view",
    ),
]
