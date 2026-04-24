#!/bin/bash
# Watchdog: pings /api/healthz. If it fails, tries to bring the panel back.
# Runs standalone OR via the watchdog plist (every 5min).
# Exit 0 = healthy, exit 1 = could not recover.

set -euo pipefail
cd "$(dirname "$0")"
HERE="$(pwd)"

if [ -f .env ]; then
  # shellcheck disable=SC1091
  set -a; source .env; set +a
fi

LABEL_PREFIX="${BOOKMARKS_LABEL_PREFIX:-com.bookmarks.panel}"
LABEL="$LABEL_PREFIX"
PORT="${BOOKMARKS_PORT:-8765}"
LOG="$HERE/data/healthcheck.log"
mkdir -p "$HERE/data"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] $*" | tee -a "$LOG"; }

if curl -sf "http://127.0.0.1:$PORT/api/healthz" >/dev/null 2>&1; then
  exit 0
fi

log "✖ panel offline on :$PORT — trying to recover"

if launchctl list 2>/dev/null | grep -q "$LABEL"; then
  log "  → kickstart via launchctl"
  launchctl kickstart -k "gui/$(id -u)/$LABEL" 2>/dev/null || true
else
  log "  → agent not loaded, running install-launchd.sh"
  ./install-launchd.sh >>"$LOG" 2>&1 || true
fi

for i in $(seq 1 20); do
  if curl -sf "http://127.0.0.1:$PORT/api/healthz" >/dev/null 2>&1; then
    log "✓ panel recovered (after ${i}s)"
    exit 0
  fi
  sleep 1
done

log "✖ could not recover. Check data/painel.err.log"
exit 1
