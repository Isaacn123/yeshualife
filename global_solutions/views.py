from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from .api_urls import video_api_urls_placeholder_map
from .b2 import b2_public_url, get_b2_s3_client
from .b2_upload import safe_upload_filename

from .discovery import (
    build_farmhub_home_context,
    get_site_title,
    get_public_videos_qs,
    get_related_videos,
    get_videos_for_category,
    search_videos,
)
from .categories import get_active_categories, resolve_category
from .engagement import video_view_counted_in_session
from .models import (
    Creator,
    GlobalSolutionsSettings,
    GlobalSolutionsVideo,
    GlobalSolutionsVideoStatus,
    SolutionCategory,
)


@dataclass(frozen=True)
class PageLike:
    title: str
    seo_title: str
    intro: str
    search_description: str
    image: None = None


# --------------------------
# Direct-to-B2 upload endpoints (staff-only)
# --------------------------


@require_GET
@staff_member_required
def upload_center(request):
    """
    Lightweight staff-only upload UI for direct-to-B2 multipart uploads.
    This avoids routing large files through Django/Wagtail admin.
    """
    settings_obj = GlobalSolutionsSettings.objects.first()
    page = PageLike(
        title="Global Solutions Upload Center",
        seo_title="Global Solutions Upload Center",
        intro="Upload large clips directly to Backblaze B2, then process to HLS for fast playback.",
        search_description="Upload Global Solutions videos",
    )
    return render(
        request,
        "global_solutions/upload_center.html",
        {
            "page": page,
            "hero_title": "Global Solutions Upload Center",
            "hero_subtitle": (settings_obj.hero_subtitle if settings_obj else "").strip(),
            "gs_video_api_urls_placeholder": video_api_urls_placeholder_map(),
            "solution_categories": get_active_categories(),
        },
    )


@require_POST
@staff_member_required
def create_video_record(request):
    category_id = (request.POST.get("category_id") or request.POST.get("category") or "").strip()
    category_slug = (request.POST.get("category_slug") or "").strip()
    title = (request.POST.get("title") or "").strip()
    description = (request.POST.get("description") or "").strip()

    category = resolve_category(category_id=category_id or None, category_slug=category_slug or None)
    if not category:
        return JsonResponse({"error": "Valid category is required"}, status=400)
    if not title:
        return JsonResponse({"error": "title is required"}, status=400)

    v = GlobalSolutionsVideo.objects.create(
        category=category,
        title=title,
        description=description,
        status=GlobalSolutionsVideoStatus.DRAFT,
        created_by=request.user,
    )
    return JsonResponse({"video_id": str(v.id)})


@require_GET
@staff_member_required
def api_deploy_check(request):
    """
    Lightweight probe so production can confirm ``global_solutions`` URLs are deployed
    (visit while logged in as staff): GET /global-solutions/api/ok/
    """
    return JsonResponse({"ok": True, "global_solutions_api": "mounted"})


@require_POST
@staff_member_required
def update_video_meta(request, video_id):
    """
    Sync kind/title/description from the Wagtail snippet form before B2 multipart upload.
    Not used for B2 credentials (those stay server-side).
    """
    try:
        video = GlobalSolutionsVideo.objects.get(pk=video_id)
    except GlobalSolutionsVideo.DoesNotExist:
        return JsonResponse(
            {
                "error": (
                    "No Global Solutions video row exists for this id in the database. "
                    "Save the snippet again on this server, or deploy/run migrations if the table is missing."
                ),
            },
            status=404,
        )
    category_id = (request.POST.get("category_id") or request.POST.get("category") or "").strip()
    category_slug = (request.POST.get("category_slug") or "").strip()
    title = (request.POST.get("title") or "").strip()
    description = (request.POST.get("description") or "").strip()

    category = resolve_category(category_id=category_id or None, category_slug=category_slug or None)
    if not category:
        return JsonResponse({"error": "Valid category is required"}, status=400)
    if not title:
        return JsonResponse({"error": "title is required"}, status=400)

    if video.status in (GlobalSolutionsVideoStatus.PROCESSING, GlobalSolutionsVideoStatus.READY):
        return JsonResponse({"error": "Cannot edit metadata while processing or ready."}, status=400)
    if video.status == GlobalSolutionsVideoStatus.UPLOADING:
        return JsonResponse({"error": "Cannot edit metadata during active upload."}, status=400)

    if video.status == GlobalSolutionsVideoStatus.UPLOADED:
        if video.category_id != category.pk:
            return JsonResponse({"error": "Cannot change category after upload."}, status=400)
        video.title = title
        video.description = description
        video.save(update_fields=["title", "description", "updated_at"])
        return JsonResponse({"ok": True})

    video.category = category
    video.title = title
    video.description = description
    video.save(update_fields=["category", "title", "description", "updated_at"])
    return JsonResponse({"ok": True})


@require_POST
@staff_member_required
def b2_create_multipart_upload(request, video_id):
    video = get_object_or_404(GlobalSolutionsVideo, pk=video_id)

    filename = safe_upload_filename(request.POST.get("filename") or "")
    content_type = (request.POST.get("content_type") or "video/mp4").strip()
    if not (request.POST.get("filename") or "").strip():
        return JsonResponse({"error": "filename is required"}, status=400)

    key = f"global-solutions/videos/{video.storage_path_slug}/{video.id}/{filename}"

    s3 = get_b2_s3_client()
    # B2 requires ContentType to be set at upload creation for correct metadata
    from .b2 import get_b2_config

    cfg = get_b2_config()
    resp = s3.create_multipart_upload(Bucket=cfg.bucket_name, Key=key, ContentType=content_type)
    upload_id = resp["UploadId"]

    video.status = GlobalSolutionsVideoStatus.UPLOADING
    video.original_b2_key = key
    video.original_content_type = content_type
    video.last_error = ""
    video.save(update_fields=["status", "original_b2_key", "original_content_type", "last_error", "updated_at"])

    return JsonResponse({"upload_id": upload_id, "key": key})


@require_POST
@staff_member_required
def b2_get_upload_part_url(request, video_id):
    video = get_object_or_404(GlobalSolutionsVideo, pk=video_id)
    upload_id = (request.POST.get("upload_id") or "").strip()
    part_number_raw = (request.POST.get("part_number") or "").strip()

    try:
        part_number = int(part_number_raw)
    except ValueError:
        return JsonResponse({"error": "part_number must be an integer"}, status=400)

    if not upload_id:
        return JsonResponse({"error": "upload_id is required"}, status=400)
    if not video.original_b2_key:
        return JsonResponse({"error": "video has no original_b2_key"}, status=400)

    s3 = get_b2_s3_client()
    from .b2 import get_b2_config

    cfg = get_b2_config()
    url = s3.generate_presigned_url(
        ClientMethod="upload_part",
        Params={"Bucket": cfg.bucket_name, "Key": video.original_b2_key, "UploadId": upload_id, "PartNumber": part_number},
        ExpiresIn=60 * 30,  # 30 minutes
        HttpMethod="PUT",
    )
    return JsonResponse({"url": url})


@require_POST
@staff_member_required
def b2_complete_multipart_upload(request, video_id):
    """
    Expects:
      - upload_id
      - parts: JSON string like [{"PartNumber":1,"ETag":"..."}]
      - size_bytes (optional)
    """
    import json

    video = get_object_or_404(GlobalSolutionsVideo, pk=video_id)
    upload_id = (request.POST.get("upload_id") or "").strip()
    parts_json = (request.POST.get("parts") or "").strip()
    size_bytes_raw = (request.POST.get("size_bytes") or "").strip()

    if not upload_id or not parts_json:
        return JsonResponse({"error": "upload_id and parts are required"}, status=400)
    if not video.original_b2_key:
        return JsonResponse({"error": "video has no original_b2_key"}, status=400)

    try:
        parts = json.loads(parts_json)
        if not isinstance(parts, list) or not parts:
            raise ValueError("parts must be a non-empty list")
    except Exception:
        return JsonResponse({"error": "parts must be valid JSON list"}, status=400)

    size_bytes = None
    if size_bytes_raw:
        try:
            size_bytes = int(size_bytes_raw)
        except ValueError:
            return JsonResponse({"error": "size_bytes must be an integer"}, status=400)

    s3 = get_b2_s3_client()
    from .b2 import get_b2_config

    cfg = get_b2_config()
    s3.complete_multipart_upload(
        Bucket=cfg.bucket_name,
        Key=video.original_b2_key,
        UploadId=upload_id,
        MultipartUpload={"Parts": parts},
    )

    video.original_size_bytes = size_bytes
    video.last_error = ""
    if getattr(settings, "GLOBAL_SOLUTIONS_TRANSCODE_HLS", False):
        video.status = GlobalSolutionsVideoStatus.UPLOADED
    else:
        video.status = GlobalSolutionsVideoStatus.READY
    video.save(update_fields=["status", "original_size_bytes", "last_error", "updated_at"])

    try:
        from .thumbnails import generate_poster_candidates

        candidates = generate_poster_candidates(video)
    except Exception:
        candidates = []

    thumb_payload = {}
    try:
        from .thumbnails import list_thumbnail_options

        thumb_payload = list_thumbnail_options(video)
    except Exception:
        thumb_payload = {"poster_url": video.thumbnail_url or "", "candidates": [], "custom": None}

    return JsonResponse(
        {
            "ok": True,
            "key": video.original_b2_key,
            "public_url": b2_public_url(video.original_b2_key),
            "poster_url": video.thumbnail_url or "",
            "candidates": candidates or thumb_payload.get("candidates") or [],
            "playback_url": video.playback_url,
        }
    )


@require_GET
@staff_member_required
def video_thumbnails(request, video_id):
    video = get_object_or_404(GlobalSolutionsVideo, pk=video_id)
    if not video.original_b2_key:
        return JsonResponse({"error": "No uploaded video yet."}, status=400)
    from .thumbnails import list_thumbnail_options

    payload = list_thumbnail_options(video)
    payload["playback_url"] = video.playback_url
    payload["ok"] = True
    return JsonResponse(payload)


@require_POST
@staff_member_required
def video_thumbnails_generate(request, video_id):
    video = get_object_or_404(GlobalSolutionsVideo, pk=video_id)
    if not video.original_b2_key:
        return JsonResponse({"error": "No uploaded video yet."}, status=400)
    from .thumbnails import (
        ThumbnailGenerationError,
        ffmpeg_diagnostic,
        generate_poster_candidates,
        list_thumbnail_options,
    )

    try:
        candidates = generate_poster_candidates(video)
    except ThumbnailGenerationError as exc:
        return JsonResponse(
            {
                "error": str(exc),
                "detail": exc.detail,
                "ffmpeg": exc.ffmpeg_path or ffmpeg_diagnostic().get("resolved"),
                "ffmpeg_diagnostic": ffmpeg_diagnostic(),
            },
            status=500,
        )
    except Exception as exc:
        return JsonResponse(
            {
                "error": str(exc),
                "ffmpeg_diagnostic": ffmpeg_diagnostic(),
            },
            status=500,
        )
    if not candidates:
        return JsonResponse(
            {
                "error": "Could not generate thumbnails.",
                "ffmpeg_diagnostic": ffmpeg_diagnostic(),
            },
            status=500,
        )
    payload = list_thumbnail_options(video)
    payload["playback_url"] = video.playback_url
    payload["ok"] = True
    return JsonResponse(payload)


@require_POST
@staff_member_required
def video_thumbnail_select(request, video_id):
    video = get_object_or_404(GlobalSolutionsVideo, pk=video_id)
    b2_key = (request.POST.get("b2_key") or "").strip()
    if not b2_key:
        return JsonResponse({"error": "b2_key is required"}, status=400)
    from .thumbnails import list_thumbnail_options, select_video_poster

    try:
        poster_url = select_video_poster(video, b2_key)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"ok": True, "poster_url": poster_url, **list_thumbnail_options(video)})


@require_POST
@staff_member_required
def video_thumbnail_upload(request, video_id):
    video = get_object_or_404(GlobalSolutionsVideo, pk=video_id)
    image = request.FILES.get("image")
    if not image:
        return JsonResponse({"error": "image file is required"}, status=400)
    from .thumbnails import list_thumbnail_options, upload_custom_poster

    try:
        custom = upload_custom_poster(video, image)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)
    return JsonResponse({"ok": True, "custom": custom, **list_thumbnail_options(video)})


@require_POST
@staff_member_required
def mark_video_processing(request, video_id):
    video = get_object_or_404(GlobalSolutionsVideo, pk=video_id)
    if getattr(settings, "GLOBAL_SOLUTIONS_TRANSCODE_HLS", False):
        if video.status not in {GlobalSolutionsVideoStatus.UPLOADED, GlobalSolutionsVideoStatus.FAILED}:
            return JsonResponse({"error": f"Cannot process from status={video.status}"}, status=400)
        video.status = GlobalSolutionsVideoStatus.PROCESSING
    else:
        if video.status == GlobalSolutionsVideoStatus.READY:
            return JsonResponse({"ok": True})
        if video.status not in {GlobalSolutionsVideoStatus.UPLOADED, GlobalSolutionsVideoStatus.FAILED}:
            return JsonResponse({"error": f"Cannot finalize from status={video.status}"}, status=400)
        video.status = GlobalSolutionsVideoStatus.READY
    video.last_error = ""
    video.save(update_fields=["status", "last_error", "updated_at"])
    return JsonResponse({"ok": True})


# --------------------------
# FarmHub public discovery pages
# --------------------------


def _farmhub_page(title: str, intro: str = ""):
    return PageLike(
        title=title,
        seo_title=title,
        intro=intro,
        search_description=intro,
    )


@require_GET
def farmhub_home(request):
    ctx = build_farmhub_home_context()
    ctx["page"] = _farmhub_page(ctx.get("hero_title", get_site_title()), ctx.get("hero_subtitle", ""))
    ctx["solution_categories"] = get_active_categories()
    return render(request, "global_solutions/farmhub_home.html", ctx)


@require_GET
def farmhub_category(request, slug):
    category = get_object_or_404(SolutionCategory, slug=slug, is_active=True)
    videos = get_videos_for_category(category, limit=48)
    ctx = {
        "page": _farmhub_page(category.name, category.description),
        "site_title": get_site_title(),
        "category": category,
        "videos": videos,
        "farmhub_home_url": request.build_absolute_uri("/farmhub/"),
    }
    return render(request, "global_solutions/category_page.html", ctx)


@require_GET
def farmhub_creator(request, slug):
    creator = get_object_or_404(Creator, slug=slug, is_active=True)
    videos = list(
        get_public_videos_qs()
        .filter(creator=creator)
        .order_by("-published_at")[:48]
    )
    ctx = {
        "page": _farmhub_page(creator.name, creator.bio),
        "site_title": get_site_title(),
        "creator": creator,
        "videos": videos,
    }
    return render(request, "global_solutions/creator_page.html", ctx)


@require_GET
def farmhub_video(request, slug):
    video = get_object_or_404(
        get_public_videos_qs(),
        slug=slug,
    )
    related = get_related_videos(video, limit=8)
    ctx = {
        "page": _farmhub_page(video.title, video.description[:300]),
        "site_title": get_site_title(),
        "video": video,
        "related_videos": related,
        "view_already_counted": video_view_counted_in_session(request, slug),
    }
    return render(request, "global_solutions/video_detail.html", ctx)


@require_GET
def farmhub_search(request):
    q = (request.GET.get("q") or "").strip()
    videos = search_videos(q, limit=48) if q else []
    ctx = {
        "page": _farmhub_page("Search", f"Results for {q}" if q else "Search farming videos"),
        "site_title": get_site_title(),
        "query": q,
        "videos": videos,
        "categories": get_active_categories(),
    }
    return render(request, "global_solutions/search_results.html", ctx)

