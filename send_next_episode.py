#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
『1000年後の名言』 自動下書き送信＆GitHub Pages同期スクリプト (send_next_episode.py)
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from render_slides import render_episode, WORKSPACE_DIR
import cloud_send_daily


def wait_for_github_pages(url: str, timeout_sec: int = 90) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(4)
    return False


def sync_git_and_pages() -> None:
    subprocess.run(
        [
            "git",
            "add",
            "episodes.json",
            ".last_sent_date",
            "render_slides.py",
            "cloud_send_daily.py",
            "send_next_episode.py",
            "docs",
        ],
        cwd=WORKSPACE_DIR,
        check=False,
    )
    subprocess.run(
        ["git", "commit", "-m", "Upgrade 018-024 to v8 direct sci-fi hook format"],
        cwd=WORKSPACE_DIR,
        check=False,
    )
    subprocess.run(
        ["git", "push", "-f", "origin", "main"],
        cwd=WORKSPACE_DIR,
        check=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="同日送信済みでも強制送信する")
    parser.add_argument("--episode", type=str, default="", help="特定の記録番号を指定して送信")
    args = parser.parse_args()

    episodes_file = WORKSPACE_DIR / "episodes.json"
    episodes = json.loads(episodes_file.read_text(encoding="utf-8"))
    target_id = args.episode.zfill(3) if args.episode else None
    if target_id:
        next_ep = next((e for e in episodes if e.get("id") == target_id), None)
    else:
        next_ep = next((e for e in episodes if e.get("status") == "ready"), None)

    if not next_ep:
        print("[INFO] 対象の未送信エピソードがありません。")
        return

    ep_id = next_ep["id"]
    theme = next_ep["theme"]
    bg_path = WORKSPACE_DIR / "backgrounds" / f"{ep_id}_bg.png"
    out_dir = WORKSPACE_DIR / "posts" / f"{ep_id}_{theme}"
    if not (WORKSPACE_DIR / "docs" / "posts" / ep_id / "01_v8.jpg").exists():
        render_episode(next_ep, out_dir, bg_path if bg_path.exists() else None)

    # まず GitHub Pages へ最新の v8 スライドを push して公開反映を確認
    sync_git_and_pages()
    test_url = f"https://miracle-tamechan0429-ops.github.io/quotes3000/posts/{ep_id}/01_v8.jpg"
    print(f"[INFO] Waiting for GitHub Pages deployment: {test_url}")
    wait_for_github_pages(test_url, timeout_sec=75)

    # TikTok 下書きへ即時送信
    sys_argv = [sys.argv[0], "--force", "--episode", ep_id]
    sys.argv = sys_argv
    try:
        cloud_send_daily.main()
    except SystemExit:
        pass

    # 送信後のステータス (019=published, 020..024=ready) を GitHub とローカルデーモンへ同期
    subprocess.run(
        ["git", "add", "episodes.json", ".last_sent_date", "docs/index.html", "LATEST_FIRST_COMMENT.txt"],
        cwd=WORKSPACE_DIR,
        check=False,
    )
    subprocess.run(
        ["git", "commit", "-m", f"Send v8 episode {ep_id} and queue 020+ for 9am"],
        cwd=WORKSPACE_DIR,
        check=False,
    )
    subprocess.run(["git", "push", "-f", "origin", "main"], cwd=WORKSPACE_DIR, check=False)
    subprocess.run(["/bin/zsh", str(WORKSPACE_DIR / "install_daemon.sh")], cwd=WORKSPACE_DIR, check=False)


if __name__ == "__main__":
    main()
