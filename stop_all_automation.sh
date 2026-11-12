#!/bin/zsh
set -e

PLIST="/Users/miraclechaplin/Library/LaunchAgents/com.quotes3000.daily.plist"
DST="/Users/miraclechaplin/.quotes3000_daemon"
SRC="/Volumes/SSD20230816/📕1000年後の名言"

if [ -f "$PLIST" ]; then
  launchctl unload -w "$PLIST" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Removed LaunchAgent plist: $PLIST"
fi

if [ -d "$DST" ]; then
  rm -rf "$DST"
  echo "Removed daemon directory: $DST"
fi

cd "$SRC"
git pull --rebase origin main || true
git add .github/workflows/daily_tiktok_draft.yml stop_all_automation.sh
git commit -m "Stop all scheduled automation for quotes3000" || true
git push origin main || true

echo "All automation stopped cleanly."
