#!/bin/zsh
set -e
SRC="/Volumes/SSD20230816/📕1000年後の名言"
DST="/Users/miraclechaplin/.quotes3000_daemon"
PLIST="/Users/miraclechaplin/Library/LaunchAgents/com.quotes3000.daily.plist"

mkdir -p "$DST/docs" "/Users/miraclechaplin/Library/LaunchAgents"
cp -Rf "$SRC/.git" "$DST/"
cp -f "$SRC/cloud_send_daily.py" "$SRC/run_daemon_check.sh" "$SRC/config.json" "$SRC/episodes.json" "$SRC/.last_sent_date" "$SRC/LATEST_FIRST_COMMENT.txt" "$DST/"
cp -f "$SRC/docs/index.html" "$DST/docs/index.html"
chmod +x "$DST/run_daemon_check.sh" "$DST/cloud_send_daily.py"

cp -f "$SRC/com.quotes3000.daily.plist" "$PLIST"
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load -w "$PLIST"
launchctl list | grep com.quotes3000.daily
echo "✅ macOS LaunchAgent (com.quotes3000.daily) installed and active!"
