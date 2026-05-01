from __future__ import annotations

from dataclasses import dataclass

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from .b2 import b2_public_url, get_b2_s3_client
from .models import (
    GlobalSolutionsBlock,
    GlobalSolutionsBlockCategory,
    GlobalSolutionsSettings,
    GlobalSolutionsVideo,
    GlobalSolutionsVideoKind,
    GlobalSolutionsVideoStatus,
)


@dataclass(frozen=True)
class PageLike:
    title: str
    seo_title: str
    intro: str
    search_description: str
    image: None = None


def build_global_solutions_public_context() -> dict:
    """Template context for the public Global Solutions page (blocks, videos, hero)."""
    settings_obj = GlobalSolutionsSettings.objects.first()
    page_title = (settings_obj.page_title if settings_obj else "Global Solutions").strip() or "Global Solutions"
    hero_title = (settings_obj.hero_title if settings_obj else page_title).strip() or page_title
    hero_subtitle = (settings_obj.hero_subtitle if settings_obj else "").strip()

    blocks_qs = GlobalSolutionsBlock.objects.filter(is_active=True)
    blocks_by_category: dict[str, list[GlobalSolutionsBlock]] = {}
    for cat, _label in GlobalSolutionsBlockCategory.choices:
        blocks_by_category[cat] = list(blocks_qs.filter(category=cat).order_by("sort_order", "-created_at"))

    videos_qs = GlobalSolutionsVideo.objects.filter(
        is_active=True,
        status=GlobalSolutionsVideoStatus.READY,
    )
    feeds = list(
        videos_qs.filter(kind=GlobalSolutionsVideoKind.FEEDING).order_by("-published_at", "sort_order")[:12]
    )
    preachings = list(
        videos_qs.filter(kind=GlobalSolutionsVideoKind.PREACHING).order_by("-published_at", "sort_order")[:12]
    )
    learning = list(
        videos_qs.filter(kind=GlobalSolutionsVideoKind.LEARNING).order_by("-published_at", "sort_order")[:12]
    )

    return {
        "hero_title": hero_title,
        "hero_subtitle": hero_subtitle,
        "hero_image_url": (settings_obj.hero_image_url if settings_obj else "").strip(),
        "blocks_by_category": blocks_by_category,
        "feeds": feeds,
        "preachings": preachings,
        "learning": learning,
    }


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
        },
    )


@require_POST
@staff_member_required
def create_video_record(request):
    kind = (request.POST.get("kind") or "").strip()
    title = (request.POST.get("title") or "").strip()
    description = (request.POST.get("description") or "").strip()

    if kind not in {k for k, _ in GlobalSolutionsVideoKind.choices}:
        return JsonResponse({"error": "Invalid kind"}, status=400)
    if not title:
        return JsonResponse({"error": "title is required"}, status=400)

    v = GlobalSolutionsVideo.objects.create(
        kind=kind,
        title=title,
        description=description,
        status=GlobalSolutionsVideoStatus.DRAFT,
        created_by=request.user,
    )
    return JsonResponse({"video_id": str(v.id)})


@require_POST
@staff_member_required
def b2_create_multipart_upload(request, video_id):
    video = get_object_or_404(GlobalSolutionsVideo, pk=video_id)

    filename = (request.POST.get("filename") or "").strip()
    content_type = (request.POST.get("content_type") or "video/mp4").strip()

    if not filename:
        return JsonResponse({"error": "filename is required"}, status=400)

    key = f"global-solutions/videos/{video.kind}/{video.id}/{filename}"

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

    video.status = GlobalSolutionsVideoStatus.UPLOADED
    video.original_size_bytes = size_bytes
    video.last_error = ""
    video.save(update_fields=["status", "original_size_bytes", "last_error", "updated_at"])

    return JsonResponse({"ok": True, "key": video.original_b2_key, "public_url": b2_public_url(video.original_b2_key)})


@require_POST
@staff_member_required
def mark_video_processing(request, video_id):
    video = get_object_or_404(GlobalSolutionsVideo, pk=video_id)
    if video.status not in {GlobalSolutionsVideoStatus.UPLOADED, GlobalSolutionsVideoStatus.FAILED}:
        return JsonResponse({"error": f"Cannot process from status={video.status}"}, status=400)
    video.status = GlobalSolutionsVideoStatus.PROCESSING
    video.last_error = ""
    video.save(update_fields=["status", "last_error", "updated_at"])
    return JsonResponse({"ok": True})

