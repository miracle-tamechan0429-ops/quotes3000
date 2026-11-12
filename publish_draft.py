#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
『1000年後の名言』 ワンコマンド半自動化パイプライン (publish_draft.py)
使い方:
  python3 publish_draft.py --id 005
  または Finder から『TikTok下書き送信.command』をダブルクリック！

実行すると以下を自動で完了します:
1. 物語専用の実写映画背景 (backgrounds/{id}_bg.png) で 5枚のスライド (01.png〜05.png & 01.jpg〜05.jpg) を生成
2. キャプション＆1コメ目アンケートを posts/{id}_{theme}/caption_and_comment.txt に出力
3. Mac/iPhone 共通のクリップボードにキャプションを自動コピー（iPhoneでそのままペースト可能）
4. iCloud Drive (『1000年後の名言』フォルダ) にも自動コピー（iPhoneの「ファイル」からいつでも即アクセス可能）
5. GitHub Pages へ自動プッシュし、TikTok公式API (MEDIA_UPLOAD) でスマホのTikTokアプリ通知（下書き）へ送信
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from render_slides import render_episode, WORKSPACE_DIR
from tiktok_uploader import load_config, upload_via_tiktok_official_api, upload_via_upload_post


def copy_to_clipboard(text: str) -> None:
    try:
        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
        print("[OK] キャプションをクリップボードにコピーしました（iPhoneでもそのままペースト可能です）")
    except Exception:
        pass


def sync_to_icloud(ep_id: str, theme: str, out_dir: Path) -> None:
    try:
        icloud_root = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
        if icloud_root.exists():
            dest = icloud_root / "1000年後の名言" / f"{ep_id}_{theme}"
            dest.mkdir(parents=True, exist_ok=True)
            for item in out_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, dest / item.name)
            print(f"[OK] iCloud Drive にも自動同期しました: {dest}")
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="1000年後の名言 半自動下書き送信パイプライン")
    parser.add_argument("--id", required=True, help="エピソード記録番号（例: 005, 007）")
    parser.add_argument("--render-only", action="store_true", help="スライド生成とクリップボードコピーのみ実行")
    args = parser.parse_args()

    episodes_file = WORKSPACE_DIR / "episodes.json"
    episodes = json.loads(episodes_file.read_text(encoding="utf-8"))
    ep = next((e for e in episodes if e["id"] == args.id), None)
    if not ep:
        print(f"エラー: 記録番号 {args.id} が episodes.json に見つかりません。")
        sys.exit(1)

    bg_path = WORKSPACE_DIR / "backgrounds" / f"{ep['id']}_bg.png"
    out_dir = WORKSPACE_DIR / "posts" / f"{ep['id']}_{ep['theme']}"

    print(f"=== Step 1: 【記録番号：{ep['id']}】（{ep['theme']}）の5枚スライドを生成 ===")
    render_episode(ep, out_dir, bg_path if bg_path.exists() else None)
    print(f"[OK] スライド出力先: {out_dir}")

    caption_full = f"{ep['tiktok']['title']}\n\n{ep['tiktok']['caption']}"
    copy_to_clipboard(caption_full)
    sync_to_icloud(ep["id"], ep["theme"], out_dir)

    print("\n--- 1コメ目（固定コメント用・意識調査） ---")
    print(ep["tiktok"]["comment"])
    print("------------------------------------------\n")

    if args.render_only:
        return

    cfg = load_config()
    if not cfg:
        return

    print("=== Step 2: TikTokアプリの受信トレイ（下書き）へ5枚の画像を送信 ===")
    provider = cfg.get("provider", "tiktok_official")
    if provider == "tiktok_official":
        upload_via_tiktok_official_api(ep, cfg)
    else:
        upload_via_upload_post(ep, out_dir, cfg)


if __name__ == "__main__":
    main()
