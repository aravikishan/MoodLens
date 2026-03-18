#!/usr/bin/env bash
# MoodLens startup script
set -euo pipefail

export PORT=${PORT:-8008}

echo "==> Installing dependencies..."
pip install -q -r requirements.txt

echo "==> Starting MoodLens on port $PORT..."
python app.py
