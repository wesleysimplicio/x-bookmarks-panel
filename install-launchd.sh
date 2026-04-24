#!/bin/bash
# Installs the panel as a macOS user agent (launchd).
# Renders plist templates from scripts/launchd/ with $HOME + label prefix,
# then bootstraps them. Idempotent.

set -euo pipefail
cd "$(dirname "$0")"
HERE="$(pwd)"

if [ -f .env ]; then
  # shellcheck disable=SC1091
  set -a; source .env; set +a
fi

LABEL_PREFIX="${BOOKMARKS_LABEL_PREFIX:-com.bookmarks.panel}"
PORT="${BOOKMARKS_PORT:-8765}"
LABEL="$LABEL_PREFIX"
WATCHDOG_LABEL="$LABEL_PREFIX-watchdog"

PLIST_TEMPLATE="$HERE/scripts/launchd/panel.plist.template"
WATCHDOG_TEMPLATE="$HERE/scripts/launchd/watchdog.plist.template"
PLIST_DST="$HOME/Library/LaunchAgents/$LABEL.plist"
WATCHDOG_DST="$HOME/Library/LaunchAgents/$WATCHDOG_LABEL.plist"

if [ ! -d .venv ]; then
  echo "✖ .venv not found. Run ./setup.sh first."
  exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$HERE/data"

render_plist() {
  local src="$1" dst="$2" label="$3"
  sed \
    -e "s|__LABEL__|$label|g" \
    -e "s|__REPO__|$HERE|g" \
    -e "s|__PORT__|$PORT|g" \
    "$src" > "$dst"
}

for L in "$LABEL" "$WATCHDOG_LABEL"; do
  if launchctl list 2>/dev/null | grep -q "$L"; then
    echo "→ Unloading previous instance: $L"
    launchctl bootout "gui/$(id -u)/$L" 2>/dev/null \
      || launchctl unload "$HOME/Library/LaunchAgents/$L.plist" 2>/dev/null \
      || true
  fi
done

echo "→ Rendering panel plist → $PLIST_DST"
render_plist "$PLIST_TEMPLATE" "$PLIST_DST" "$LABEL"
echo "→ Rendering watchdog plist → $WATCHDOG_DST"
render_plist "$WATCHDOG_TEMPLATE" "$WATCHDOG_DST" "$WATCHDOG_LABEL"

echo "→ Loading panel into launchd"
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
echo "→ Loading watchdog into launchd"
launchctl bootstrap "gui/$(id -u)" "$WATCHDOG_DST"

launchctl kickstart -k "gui/$(id -u)/$LABEL" 2>/dev/null || true

echo -n "→ Waiting for server on :$PORT "
for i in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:$PORT/api/healthz" >/dev/null 2>&1; then
    echo " OK"
    echo ""
    echo "✓ Panel running at http://localhost:$PORT"
    echo "✓ Watchdog active (pings every 5min, restarts on failure)"
    echo ""
    echo "Useful commands:"
    echo "  launchctl list | grep $LABEL_PREFIX   # check status"
    echo "  tail -f data/painel.log                # server logs"
    echo "  tail -f data/healthcheck.log           # watchdog logs"
    echo "  ./stop.sh                              # stop everything"
    exit 0
  fi
  sleep 1; printf "."
done

echo ""
echo "✖ Server did not respond in 30s."
echo "  Check logs:"
echo "    tail -n 50 data/painel.err.log"
exit 1
