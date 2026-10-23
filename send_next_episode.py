#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
『1000年後の名言』 毎朝9時 自動下書き送信＆ステータス更新スクリプト (send_next_episode.py)
- cloud_send_daily.py と完全連携し、クラウド(GitHub Actions)・Macバックグラウンド(launchd)・Antigravityの間で
  二重送信を防ぎつつ、毎朝9時に未送信エピソードをTikTokの下書き（MEDIA_UPLOAD）へ送信する。
"""

import argparse
import json
import sys
from pathlib import Path

from render_slides import render_episode, WORKSPACE_DIR
import cloud_send_daily


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="同日送信済みでも強制送信する")
    args = parser.parse_args()

    # もしローカルで未レンダリングのエピソードがあれば事前に生成しておく
    episodes_file = WORKSPACE_DIR / "episodes.json"
    if episodes_file.exists():
        episodes = json.loads(episodes_file.read_text(encoding="utf-8"))
        next_ep = next((e for e in episodes if e.get("status") == "ready"), None)
        if next_ep:
            ep_id = next_ep["id"]
            theme = next_ep["theme"]
            bg_path = WORKSPACE_DIR / "backgrounds" / f"{ep_id}_bg.png"
            out_dir = WORKSPACE_DIR / "posts" / f"{ep_id}_{theme}"
            if not (out_dir / "01.png").exists():
                render_episode(next_ep, out_dir, bg_path if bg_path.exists() else None)

    sys_argv = [sys.argv[0], "--git-sync"]
    if args.force:
        sys_argv.append("--force")
    sys.argv = sys_argv
    cloud_send_daily.main()


if __name__ == "__main__":
    main()
