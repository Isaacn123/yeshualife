#!/usr/bin/env bash
# One-shot production deploy for FarmHub + SolutionCategory migration.
# Run on the server as the deploy user, from the project root.
#
# Usage:
#   cd /var/www/yeshualife
#   bash deploy/production-farmhub-once.sh
#
# Optional env overrides:
#   VENV_PYTHON=/root/n/bin/python
#   GUNICORN_SERVICE=gunicorn   # or yeshualife, etc. — set empty to skip restart

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/var/www/yeshualife}"
VENV_PYTHON="${VENV_PYTHON:-python}"
GUNICORN_SERVICE="${GUNICORN_SERVICE:-}"

cd "$PROJECT_DIR"

echo "==> Project: $PROJECT_DIR"
echo "==> Python: $($VENV_PYTHON --version)"

echo "==> Pull latest code (skip if you deploy another way)"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git pull --ff-only || echo "WARN: git pull failed — continuing with current tree"
fi

echo "==> Install dependencies"
if [ -f requirements.txt ]; then
  $VENV_PYTHON -m pip install -r requirements.txt -q
fi

echo "==> Django check"
$VENV_PYTHON manage.py check

echo "==> Migrate (global_solutions 0005 — categories, removes kind)"
$VENV_PYTHON manage.py migrate global_solutions --noinput

echo "==> Collect static files"
$VENV_PYTHON manage.py collectstatic --noinput

echo "==> Restart app"
if [ -n "$GUNICORN_SERVICE" ] && command -v systemctl >/dev/null 2>&1; then
  sudo systemctl restart "$GUNICORN_SERVICE"
  echo "    Restarted $GUNICORN_SERVICE"
else
  echo "    Set GUNICORN_SERVICE=your-unit to restart (e.g. GUNICORN_SERVICE=gunicorn bash $0)"
fi

if command -v systemctl >/dev/null 2>&1 && systemctl is-enabled global-solutions-video-worker.service >/dev/null 2>&1; then
  sudo systemctl restart global-solutions-video-worker.service || true
fi

echo "==> Generate missing video posters (requires ffmpeg on server)"
$VENV_PYTHON manage.py generate_video_posters --limit 50 || echo "WARN: poster generation skipped or partial"

echo "==> Smoke tests (adjust host if needed)"
BASE="${SMOKE_BASE_URL:-https://yeshualifeug.com}"
for path in \
  "/farmhub/" \
  "/api/categories/" \
  "/global-solutions/api/ok/" \
  ; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE$path" || echo "000")
  echo "    $code  $BASE$path"
done

echo ""
echo "Done. Next steps in Wagtail admin:"
echo "  1. Snippets → Solution categories — review Feeding, Preaching, Crop Farming, etc."
echo "  2. Snippets → Global Solutions videos — confirm each video has a Category"
echo "  3. Open $BASE/farmhub/ in the browser"
