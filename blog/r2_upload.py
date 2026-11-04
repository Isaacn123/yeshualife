"""Direct browser uploads to Cloudflare R2 for event videos."""

from __future__ import annotations

import re
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings


class R2NotConfigured(Exception):
    pass


def safe_upload_filename(filename: str) -> str:
    name = Path((filename or "").strip()).name
    if not name:
        return "video.mp4"
    stem = Path(name).stem
    ext = Path(name).suffix.lower()
    if ext not in {".mp4", ".mov", ".m4v", ".webm"}:
        ext = ".mp4"
    safe_stem = re.sub(r"[^\w\-]+", "-", stem).strip("-").lower() or "video"
    return f"{safe_stem}{ext}"


def r2_is_configured() -> bool:
    return bool(getattr(settings, "USE_R2_MEDIA", False)) and bool(
        getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")
    )


def r2_public_url(key: str) -> str:
    key = (key or "").lstrip("/")
    if not key:
        return ""
    base = (getattr(settings, "MEDIA_URL", "") or "/media/").rstrip("/")
    return f"{base}/{key}"


def get_r2_client():
    if not r2_is_configured():
        raise R2NotConfigured(
            "R2 storage is not configured. Set USE_R2_MEDIA and the R2_* values on the server."
        )
    config_kwargs = {
        "signature_version": "s3v4",
        "s3": {"addressing_style": "path"},
    }
    try:
        config = Config(
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
            **config_kwargs,
        )
    except TypeError:
        config = Config(**config_kwargs)
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=getattr(settings, "AWS_S3_REGION_NAME", "auto") or "auto",
        config=config,
    )


def r2_bucket() -> str:
    if not r2_is_configured():
        raise R2NotConfigured(
            "R2 storage is not configured. Set USE_R2_MEDIA and the R2_* values on the server."
        )
    return settings.AWS_STORAGE_BUCKET_NAME


def quote_etag(etag: str) -> str:
    etag = (etag or "").strip()
    if not etag:
        return ""
    if not etag.startswith('"'):
        etag = f'"{etag}"'
    return etag


def list_uploaded_parts(client, *, bucket: str, key: str, upload_id: str) -> list[dict]:
    parts = []
    token = None
    while True:
        kwargs = {"Bucket": bucket, "Key": key, "UploadId": upload_id}
        if token:
            kwargs["PartNumberMarker"] = token
        resp = client.list_parts(**kwargs)
        for part in resp.get("Parts") or []:
            parts.append(
                {"PartNumber": part["PartNumber"], "ETag": quote_etag(part["ETag"])}
            )
        if not resp.get("IsTruncated"):
            break
        token = resp.get("NextPartNumberMarker")
        if not token:
            break
    return parts


R2_ERRORS = (R2NotConfigured, ClientError, BotoCoreError)
