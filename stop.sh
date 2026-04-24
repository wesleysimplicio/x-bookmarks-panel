#!/bin/bash
# Stops the panel + watchdog (launchd or foreground).
# Reads label prefix from .env (BOOKMARKS_LABEL_PREFIX) or falls back to default.

set -euo pipefail
cd "$(dirname "$0")"

if [ -f .env ]; then
  # shellcheck disable=SC1091
  set -a; source .env; set +a
fi

LABEL_PREFIX="${BOOKMARKS_LABEL_PREFIX:-com.bookmarks.panel}"
PORT="${BOOKMARKS_PORT:-8765}"
LABEL="$LABEL_PREFIX"
WATCHDOG_LABEL="$LABEL_PREFIX-watchdog"

for L in "$LABEL" "$WATCHDOG_LABEL"; do
  if launchctl list 2>/dev/null | grep -q "$L"; then
    echo "→ Unloading $L"
    launchctl bootout "gui/$(id -u)/$L" 2>/dev/null \
      || launchctl unload "$HOME/Library/LaunchAgents/$L.plist" 2>/dev/null \
      || true
  fi
done

PIDS=$(lsof -ti ":$PORT" 2>/dev/null || true)
if [ -n "$PIDS" ]; then
  echo "→ Killing process(es) on port $PORT: $PIDS"
  kill $PIDS 2>/dev/null || true
fi

echo "✓ Panel stopped."
echo ""
echo "To start again:"
echo "  ./install-launchd.sh   # background (always-on)"
echo "  ./start.sh             # foreground (debug)"
