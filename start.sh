#!/bin/bash
# Starts the server in foreground. Ctrl+C to stop.
# For background, use the launchd plist (./install-launchd.sh).

set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "✖ .venv not found. Run ./setup.sh first."
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate
cd server
exec python app.py
