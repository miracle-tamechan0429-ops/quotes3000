#!/bin/zsh
# 『1000年後の名言』 macOS 常駐・スリープ復帰対応ランチャー
# - macOSの外部ドライブ権限ブロック(TCC)を回避するため、ホームディレクトリ直下 (~/.quotes3000_daemon) で完全自立動作
# - GitHubクラウドサーバーと git pull / git push で状態を完全同期

export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export LANG="ja_JP.UTF-8"

INT_DIR="$HOME/.quotes3000_daemon"
cd "$INT_DIR" || exit 1
/usr/bin/python3 "$INT_DIR/cloud_send_daily.py" --after-9am --git-sync
