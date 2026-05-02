#!/usr/bin/env bash
# build.sh — run by Render / Railway as the build command
# Usage: bash build.sh
set -e

echo "▶ Installing dependencies..."
pip install -r requirements.txt

echo "▶ Collecting static files..."
python manage.py collectstatic --noinput

echo "▶ Applying database migrations..."  # Fix 3
python manage.py migrate --noinput

echo "✅ Build complete."
