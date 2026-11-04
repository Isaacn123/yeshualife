"""Staff upload + public engagement for Response page videos."""

from __future__ import annotations

import json

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import F, Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from global_solutions.b2 import b2_public_url, get_b2_config, get_b2_s3_client
from global_solutions.b2_upload import safe_upload_filename
from global_solutions.engagement import (
    TRACKING_COOKIE_MAX_AGE,
    TRACKING_COOKIE_MAX_SLUGS,
    apply_view_tracking_cookie,
    session_slugs,
    view_threshold_seconds,
)

from .models import karamojaResponsePage
from .video_models import ResponsePageVideo, ResponsePageVideoStatus

LIKED_SESSION_KEY = "response_video_liked"
PLAYED_SESSION_KEY = "response_video_viewed"
PLAYED_COOKIE_NAME = "rv_viewed_videos"


def _clear_derived(video: ResponsePageVideo) -> list[str]:
    video.poster_b2_key = ""
    video.poster_image_url = ""
    video.duration_seconds = None
    video.resolution_label = ""
    return ["poster_b2_key", "poster_image_url", "duration_seconds", "resolution_label"]


def _video_payload(video: ResponsePageVideo) -> dict:
    from .api_urls import response_video_api_urls_for

    return {
        "id": str(video.id),
        "title": video.title,
        "slug": video.slug,
        "status": video.status,
        "has_video": bool((video.original_b2_key or "").strip()),
        "thumbnail_url": video.thumbnail_url or "",
        "views_display": video.views_display,
        "likes_display": video.likes_display,
        "shares_display": video.shares_display,
        "api_urls": response_video_api_urls_for(video.id),
        "public_url": video.get_absolute_url(),
    }


@require_POST
@staff_member_required
def create_video(request, page_id: int):
    page = get_object_or_404(karamojaResponsePage, pk=page_id)
    title = (request.POST.get("title") or "").strip() or "Untitled video"
    max_order = page.response_videos.aggregate(m=Max("sort_order")).get("m") or 0
    video = ResponsePageVideo(
        page=page,
        title=title,
        sort_order=max_order + 1,
        created_by=request.user if request.user.is_authenticated else None,
        status=ResponsePageVideoStatus.DRAFT,
    )
    video.save()
    return JsonResponse({"ok": True, "video": _video_payload(video)})


@require_POST
@staff_member_required
def delete_video(request, video_id):
    video = get_object_or_404(ResponsePageVideo, pk=video_id)
    video.delete()
    return JsonResponse({"ok": True})


@require_POST
@staff_member_required
def update_video_meta(request, video_id):
    video = get_object_or_404(ResponsePageVideo, pk=video_id)
    title = (request.POST.get("title") or "").strip()
    if title:
        video.title = title[:200]
        video.save(update_fields=["title", "updated_at"])
    sort_raw = (request.POST.get("sort_order") or "").strip()
    if sort_raw.isdigit():
        video.sort_order = int(sort_raw)
        video.save(update_fields=["sort_order", "updated_at"])
    return JsonResponse({"ok": True, "video": _video_payload(video)})


@require_POST
@staff_member_required
def b2_create_multipart(request, video_id):
    video = get_object_or_404(ResponsePageVideo, pk=video_id)
    filename = safe_upload_filename(request.POST.get("filename") or "")
    content_type = (request.POST.get("content_type") or "video/mp4").strip()
    if not (request.POST.get("filename") or "").strip():
        return JsonResponse({"error": "filename is required"}, status=400)

    key = f"karamoja-response/videos/{video.page_id}/{video.id}/{filename}"
    replacing = bool((video.original_b2_key or "").strip())
    s3 = get_b2_s3_client()
    cfg = get_b2_config()
    resp = s3.create_multipart_upload(Bucket=cfg.bucket_name, Key=key, ContentType=content_type)
    upload_id = resp["UploadId"]

    video.status = ResponsePageVideoStatus.UPLOADING
    video.original_b2_key = key
    video.original_content_type = content_type
    video.last_error = ""
    update_fields = ["status", "original_b2_key", "original_content_type", "last_error", "updated_at"]
    if replacing:
        update_fields.extend(_clear_derived(video))
    video.save(update_fields=update_fields)
    return JsonResponse({"upload_id": upload_id, "key": key})


@require_POST
@staff_member_required
def b2_part_url(request, video_id):
    video = get_object_or_404(ResponsePageVideo, pk=video_id)
    upload_id = (request.POST.get("upload_id") or "").strip()
    try:
        part_number = int((request.POST.get("part_number") or "").strip())
    except ValueError:
        return JsonResponse({"error": "part_number must be an integer"}, status=400)
    if not upload_id:
        return JsonResponse({"error": "upload_id is required"}, status=400)
    if not video.original_b2_key:
        return JsonResponse({"error": "video has no original_b2_key"}, status=400)

    s3 = get_b2_s3_client()
    cfg = get_b2_config()
    url = s3.generate_presigned_url(
        ClientMethod="upload_part",
        Params={
            "Bucket": cfg.bucket_name,
            "Key": video.original_b2_key,
            "UploadId": upload_id,
            "PartNumber": part_number,
        },
        ExpiresIn=60 * 30,
        HttpMethod="PUT",
    )
    return JsonResponse({"url": url})


@require_POST
@staff_member_required
def b2_complete_multipart(request, video_id):
    video = get_object_or_404(ResponsePageVideo, pk=video_id)
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
    cfg = get_b2_config()
    s3.complete_multipart_upload(
        Bucket=cfg.bucket_name,
        Key=video.original_b2_key,
        UploadId=upload_id,
        MultipartUpload={"Parts": parts},
    )

    video.original_size_bytes = size_bytes
    video.last_error = ""
    video.status = ResponsePageVideoStatus.READY
    video.save(update_fields=["status", "original_size_bytes", "last_error", "updated_at"])

    try:
        from global_solutions.thumbnails import generate_poster_candidates

        candidates = generate_poster_candidates(video)
    except Exception:
        candidates = []

    try:
        from global_solutions.thumbnails import list_thumbnail_options

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
    video = get_object_or_404(ResponsePageVideo, pk=video_id)
    if not video.original_b2_key:
        return JsonResponse({"error": "No uploaded video yet."}, status=400)
    from global_solutions.thumbnails import list_thumbnail_options

    payload = list_thumbnail_options(video)
    payload["playback_url"] = video.playback_url
    payload["ok"] = True
    return JsonResponse(payload)


@require_POST
@staff_member_required
def video_thumbnails_generate(request, video_id):
    video = get_object_or_404(ResponsePageVideo, pk=video_id)
    if not video.original_b2_key:
        return JsonResponse({"error": "No uploaded video yet."}, status=400)
    from global_solutions.thumbnails import (
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
            },
            status=500,
        )
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)
    if not candidates:
        return JsonResponse({"error": "Could not generate thumbnails."}, status=500)
    payload = list_thumbnail_options(video)
    payload["playback_url"] = video.playback_url
    payload["ok"] = True
    return JsonResponse(payload)


@require_POST
@staff_member_required
def video_thumbnail_select(request, video_id):
    video = get_object_or_404(ResponsePageVideo, pk=video_id)
    b2_key = (request.POST.get("b2_key") or "").strip()
    if not b2_key:
        return JsonResponse({"error": "b2_key is required"}, status=400)
    from global_solutions.thumbnails import list_thumbnail_options, select_video_poster

    try:
        poster_url = select_video_poster(video, b2_key)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"ok": True, "poster_url": poster_url, **list_thumbnail_options(video)})


@require_POST
@staff_member_required
def video_thumbnail_upload(request, video_id):
    video = get_object_or_404(ResponsePageVideo, pk=video_id)
    image = request.FILES.get("image")
    if not image:
        return JsonResponse({"error": "image file is required"}, status=400)
    from global_solutions.thumbnails import list_thumbnail_options, upload_custom_poster

    try:
        custom = upload_custom_poster(video, image)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)
    return JsonResponse({"ok": True, "custom": custom, **list_thumbnail_options(video)})


def _get_ready_video(slug: str) -> ResponsePageVideo:
    return get_object_or_404(
        ResponsePageVideo.objects.filter(
            is_active=True,
            status=ResponsePageVideoStatus.READY,
        ).exclude(original_b2_key=""),
        slug=slug,
    )


def _cookie_slugs(request, cookie_name: str) -> list[str]:
    raw = (request.COOKIES.get(cookie_name) or "").strip()
    if not raw:
        return []
    slugs = []
    for part in raw.split(","):
        slug = part.strip()
        if slug and slug not in slugs:
            slugs.append(slug)
    return slugs[:TRACKING_COOKIE_MAX_SLUGS]


def _mark_played(request, slug: str) -> None:
    slugs = session_slugs(request, PLAYED_SESSION_KEY)
    slugs.add(slug)
    request.session[PLAYED_SESSION_KEY] = sorted(slugs)
    request.session.modified = True
    existing = _cookie_slugs(request, PLAYED_COOKIE_NAME)
    ordered = existing if slug in existing else existing + [slug]
    if len(ordered) > TRACKING_COOKIE_MAX_SLUGS:
        ordered = ordered[-TRACKING_COOKIE_MAX_SLUGS:]
    pending = getattr(request, "_fh_tracking_cookies", {})
    pending[PLAYED_COOKIE_NAME] = ",".join(ordered)
    request._fh_tracking_cookies = pending


@csrf_protect
@require_POST
def api_video_like(request, slug):
    video = _get_ready_video(slug)
    liked = session_slugs(request, LIKED_SESSION_KEY)
    if slug in liked:
        return JsonResponse(
            {
                "slug": video.slug,
                "likes": video.likes,
                "likes_display": video.likes_display,
                "liked": True,
                "already_liked": True,
            }
        )
    ResponsePageVideo.objects.filter(pk=video.pk).update(likes=F("likes") + 1)
    video.likes += 1
    liked.add(slug)
    request.session[LIKED_SESSION_KEY] = sorted(liked)
    request.session.modified = True
    return JsonResponse(
        {
            "slug": video.slug,
            "likes": video.likes,
            "likes_display": video.likes_display,
            "liked": True,
            "already_liked": False,
        }
    )


@csrf_protect
@require_POST
def api_video_share(request, slug):
    video = _get_ready_video(slug)
    ResponsePageVideo.objects.filter(pk=video.pk).update(shares=F("shares") + 1)
    video.shares += 1
    return JsonResponse(
        {
            "slug": video.slug,
            "shares": video.shares,
            "shares_display": video.shares_display,
            "counted": True,
        }
    )


@csrf_protect
@require_POST
def api_video_view(request, slug):
    video = _get_ready_video(slug)
    try:
        body = json.loads(request.body.decode("utf-8") if request.body else "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        body = {}
    try:
        watched_seconds = float(body.get("watched_seconds", 0))
    except (TypeError, ValueError):
        watched_seconds = 0.0

    threshold = view_threshold_seconds(video.duration_seconds)
    payload = {
        "slug": video.slug,
        "views": video.views,
        "views_display": video.views_display,
        "threshold_seconds": threshold,
    }

    if watched_seconds < threshold:
        response = JsonResponse(
            {**payload, "counted": False, "error": "insufficient_watch_time", "watched_seconds": watched_seconds},
            status=400,
        )
        return response

    played = session_slugs(request, PLAYED_SESSION_KEY) | set(_cookie_slugs(request, PLAYED_COOKIE_NAME))
    if slug in played:
        response = JsonResponse({**payload, "counted": False, "already_counted": True})
        return apply_view_tracking_cookie(request, response)

    ResponsePageVideo.objects.filter(pk=video.pk).update(views=F("views") + 1)
    video.views += 1
    _mark_played(request, slug)
    payload["views"] = video.views
    payload["views_display"] = video.views_display
    response = JsonResponse({**payload, "counted": True})
    return apply_view_tracking_cookie(request, response)
