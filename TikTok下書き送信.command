#!/bin/zsh
cd "$(dirname "$0")"
echo "=================================================="
echo "  『1000年後の名言』 TikTok下書き即時送信（繰り上げ対応）"
echo "=================================================="
echo ""
read "ep_id?送信する記録番号を入力（空欄でEnterを押すと「次の未送信エピソード」を繰り上げ送信します）: "
if [[ -z "$ep_id" ]]; then
  python3 cloud_send_daily.py --force --git-sync
else
  python3 cloud_send_daily.py --episode "$ep_id" --git-sync
fi
echo ""
echo "完了しました！（明日朝9時の自動送信は自動的に次の番号へ繰り上がります）"
read
