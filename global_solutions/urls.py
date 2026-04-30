from django.urls import path

from . import views


app_name = "global_solutions"


urlpatterns = [
    path("global-solutions/", views.global_solutions_page, name="page"),
    path("global-solutions/upload/", views.upload_center, name="upload_center"),
    # Staff-only API for direct-to-B2 uploads + processing triggers
    path(
        "global-solutions/api/videos/create/",
        views.create_video_record,
        name="create_video",
    ),
    path(
        "global-solutions/api/videos/<uuid:video_id>/b2/multipart/create/",
        views.b2_create_multipart_upload,
        name="b2_create_multipart",
    ),
    path(
        "global-solutions/api/videos/<uuid:video_id>/b2/multipart/part-url/",
        views.b2_get_upload_part_url,
        name="b2_part_url",
    ),
    path(
        "global-solutions/api/videos/<uuid:video_id>/b2/multipart/complete/",
        views.b2_complete_multipart_upload,
        name="b2_complete_multipart",
    ),
    path(
        "global-solutions/api/videos/<uuid:video_id>/process/start/",
        views.mark_video_processing,
        name="process_start",
    ),
]

