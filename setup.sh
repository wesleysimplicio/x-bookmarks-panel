#!/bin/bash
# One-shot setup. Idempotent: run as many times as you like.
# venv → deps → SQLite → import (if HTML present) → register launchd → kickstart.

set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f .env ] && [ -f .env.example ]; then
  echo "→ Creating .env from .env.example (edit before production)"
  cp .env.example .env
fi

echo "→ Creating venv at .venv/"
if ! command -v python3 >/dev/null 2>&1; then
  echo "✖ python3 not found. Install: brew install python"; exit 1
fi
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

echo "→ Installing deps"
pip install --quiet --upgrade pip
pip install --quiet -r server/requirements.txt

echo "→ Init SQLite + import from HTML (if present)"
cd server
python -c "import db, importer; db.init_db()
try: print(importer.import_html())
except FileNotFoundError as e: print('(skip import)', e)"
cd ..

chmod +x start.sh stop.sh install-launchd.sh healthcheck.sh

echo ""
echo "→ Registering launchd user agents (always-on)"
./install-launchd.sh
