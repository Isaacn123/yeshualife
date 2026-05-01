# Global Solutions app

Adds a new standalone page at `/global-solutions/` with admin-manageable sections and fast video playback.

## What it includes

- **Frontend page**: `/global-solutions/`
  - Section 1: **Feeding / Preachings / Learning** (video clips)
  - Sections 2–4 + Education/Knowledge: curated blocks editable in Django admin
- **Upload Center (staff-only)**: `/global-solutions/upload/`
  - Upload large clips **direct-to-Backblaze B2** using **multipart** (no Django server bottleneck)
  - Then mark clips **PROCESSING**
- **Worker command**: converts MP4 → **HLS** for smooth playback, uploads HLS back to B2, marks clips **READY**

## Environment variables (Backblaze B2 S3-compatible)

Set these in your server environment (not in git):

- `B2_S3_ENDPOINT`
  - Example: `https://s3.us-west-002.backblazeb2.com`
- `B2_REGION`
  - Example: `us-west-002`
- `B2_BUCKET`
  - Example: `yeshualife-media`
- `B2_KEY_ID`
- `B2_APP_KEY`
- `B2_PUBLIC_BASE_URL`
  - This should point to your **CDN base** if you use Cloudflare, otherwise a direct public base URL.
  - The code builds playback URLs as: `B2_PUBLIC_BASE_URL/B2_BUCKET/<key>`

Optional:
- `FFMPEG_BIN` (default: `ffmpeg`)

## Upload & processing flow (no manual commands)

1. Visit the upload center as a staff user (recommended: Wagtail admin menu).
2. Choose type (Feeding/Preachings/Learning), set title, select file, click **Upload to B2**.
3. Click **Mark for Processing**.
4. A background worker converts MP4 → **HLS**, uploads HLS back to B2, and marks the clip **READY**.

When processing completes, the clip will show on `/global-solutions/`.

## ffmpeg requirement

The processing command requires **ffmpeg** available on the server PATH (or via `FFMPEG_BIN`).

## Running the background worker (server setup, one-time)

Run this as a long-running process (e.g. systemd):

```bash
python manage.py process_global_solutions_videos_worker
```

