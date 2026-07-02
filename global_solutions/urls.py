from django.urls import path
from django.views.generic import RedirectView

from . import api, views


app_name = "global_solutions"

_redirect = lambda pattern_name: RedirectView.as_view(
    pattern_name=pattern_name,
    permanent=True,
    query_string=True,
)

urlpatterns = [
    # Public discovery hub (canonical URLs)
    path("global-solutions/", views.farmhub_home, name="farmhub_home"),
    path("global-solutions/search/", views.farmhub_search, name="farmhub_search"),
    path("global-solutions/category/<slug:slug>/", views.farmhub_category, name="farmhub_category"),
    path("global-solutions/creator/<slug:slug>/", views.farmhub_creator, name="farmhub_creator"),
    path("global-solutions/video/<slug:slug>/", views.farmhub_video, name="farmhub_video"),
    # Legacy /farmhub/ URLs → permanent redirects
    path("farmhub/", _redirect("global_solutions:farmhub_home")),
    path("farmhub/search/", _redirect("global_solutions:farmhub_search")),
    path("farmhub/category/<slug:slug>/", _redirect("global_solutions:farmhub_category")),
    path("farmhub/creator/<slug:slug>/", _redirect("global_solutions:farmhub_creator")),
    path("farmhub/video/<slug:slug>/", _redirect("global_solutions:farmhub_video")),
    # Public read API
    path("api/videos/", api.api_videos_list, name="api_videos_list"),
    path("api/videos/trending/", api.api_videos_trending, name="api_videos_trending"),
    path("api/videos/latest/", api.api_videos_latest, name="api_videos_latest"),
    path("api/videos/featured/", api.api_videos_featured, name="api_videos_featured"),
    path("api/videos/recommended/", api.api_videos_recommended, name="api_videos_recommended"),
    path("api/videos/search/", api.api_videos_search, name="api_videos_search"),
    path("api/videos/<slug:slug>/like/", api.api_video_like, name="api_video_like"),
    path("api/videos/<slug:slug>/view/", api.api_video_record_view, name="api_video_record_view"),
    path("api/videos/category/<slug:slug>/", api.api_videos_category, name="api_videos_category"),
    path("api/categories/", api.api_categories_list, name="api_categories_list"),
    path("api/creators/", api.api_creators_list, name="api_creators_list"),
    # Staff upload (unchanged)
    path("global-solutions/upload/", views.upload_center, name="upload_center"),
    path(
        "global-solutions/api/ok/",
        views.api_deploy_check,
        name="api_deploy_check",
    ),
    path(
        "global-solutions/api/videos/create/",
        views.create_video_record,
        name="create_video",
    ),
    path(
        "global-solutions/api/videos/<uuid:video_id>/meta/",
        views.update_video_meta,
        name="update_video_meta",
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
    path(
        "global-solutions/api/videos/<uuid:video_id>/thumbnails/",
        views.video_thumbnails,
        name="video_thumbnails",
    ),
    path(
        "global-solutions/api/videos/<uuid:video_id>/thumbnails/generate/",
        views.video_thumbnails_generate,
        name="video_thumbnails_generate",
    ),
    path(
        "global-solutions/api/videos/<uuid:video_id>/thumbnails/select/",
        views.video_thumbnail_select,
        name="video_thumbnail_select",
    ),
    path(
        "global-solutions/api/videos/<uuid:video_id>/thumbnails/upload/",
        views.video_thumbnail_upload,
        name="video_thumbnail_upload",
    ),
]
