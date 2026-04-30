from __future__ import annotations

import os
from dataclasses import dataclass

import boto3
from botocore.client import Config


@dataclass(frozen=True)
class B2Config:
    endpoint_url: str
    region_name: str
    bucket_name: str
    access_key_id: str
    secret_access_key: str
    public_base_url: str


def get_b2_config() -> B2Config:
    """
    Backblaze B2 (S3-compatible) configuration from env vars.

    Required:
      - B2_S3_ENDPOINT (e.g. https://s3.us-west-002.backblazeb2.com)
      - B2_REGION (e.g. us-west-002)
      - B2_BUCKET
      - B2_KEY_ID
      - B2_APP_KEY
      - B2_PUBLIC_BASE_URL (CDN or bucket public base URL used for playback)
    """
    return B2Config(
        endpoint_url=os.environ["B2_S3_ENDPOINT"],
        region_name=os.environ.get("B2_REGION", "us-west-002"),
        bucket_name=os.environ["B2_BUCKET"],
        access_key_id=os.environ["B2_KEY_ID"],
        secret_access_key=os.environ["B2_APP_KEY"],
        public_base_url=os.environ["B2_PUBLIC_BASE_URL"].rstrip("/"),
    )


def get_b2_s3_client():
    cfg = get_b2_config()
    return boto3.client(
        "s3",
        endpoint_url=cfg.endpoint_url,
        region_name=cfg.region_name,
        aws_access_key_id=cfg.access_key_id,
        aws_secret_access_key=cfg.secret_access_key,
        config=Config(signature_version="s3v4"),
    )


def b2_public_url(key: str) -> str:
    cfg = get_b2_config()
    return f"{cfg.public_base_url}/{cfg.bucket_name}/{key.lstrip('/')}"

