#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok『1000年後の名言』 5枚カルーセル下書き自動送信スクリプト
対応モード:
1. Upload-Post API モード (推奨・ローカル画像 01.png〜05.png を直接送信可能・ドメイン認証不要)
2. TikTok 公式 Content Posting API モード (MEDIA_UPLOAD でTikTokアプリの受信トレイ/下書きへ直接通知)
"""

import argparse
import http.server
import json
import os
import sys
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = WORKSPACE_DIR / "config.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def upload_via_upload_post(ep: dict, post_dir: Path, cfg: dict) -> None:
    """
    Upload-Post API (https://api.upload-post.com/api/upload_photos) を使って
    ローカルの 01.png〜05.png を直接 TikTok に送信する。
    """
    api_key = cfg.get("upload_post_api_key") or os.environ.get("UPLOAD_POST_API_KEY")
    user_profile = cfg.get("upload_post_user") or os.environ.get("UPLOAD_POST_USER")
    if not api_key or not user_profile:
        raise ValueError("config.json に 'upload_post_api_key' と 'upload_post_user' を設定してください。")

    slides = [post_dir / f"0{i}.png" for i in range(1, 6)]
    for s in slides:
        if not s.exists():
            raise FileNotFoundError(f"スライド画像が見つかりません: {s}")

    # Multipart form-data upload using curl for maximum reliability
    import subprocess
    cmd = [
        "curl", "-sS", "-X", "POST",
        "https://api.upload-post.com/api/upload_photos",
        "-H", f"Authorization: Apikey {api_key}",
        "-F", f"user={user_profile}",
        "-F", "platform[]=tiktok",
        "-F", f"title={ep['tiktok']['title']}",
        "-F", f"description={ep['tiktok']['caption']}",
        "-F", "post_mode=MEDIA_UPLOAD",  # TikTokアプリの下書き（受信トレイ）へ送る
    ]
    for s in slides:
        cmd.extend(["-F", f"photos[]=@{s}"])

    print(f"[Upload-Post] 【記録番号：{ep['id']}】の5枚画像をTikTok下書きへ送信中...")
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    print("Response:", res.stdout or res.stderr)


def upload_via_tiktok_official_api(ep: dict, cfg: dict) -> None:
    """
    TikTok 公式 Content Posting API (/v2/post/publish/content/init/)
    post_mode="MEDIA_UPLOAD", media_type="PHOTO" により TikTok アプリの受信トレイ（下書き）へ直接送信する。
    ※公式APIの仕様上、photo_images には検証済みURLプレフィックス上のJPEG画像URLが必要です。
    """
    import subprocess
    ep_id = ep["id"]

    if cfg.get("auto_git_push", False):
        print(f"[GitHub Pages] docs/posts/{ep_id}/01.jpg〜05.jpg をGitHubへ自動プッシュ中...")
        subprocess.run(["git", "add", f"docs/posts/{ep_id}"], cwd=WORKSPACE_DIR, check=False)
        subprocess.run(["git", "commit", "-m", f"Publish slides for episode {ep_id}"], cwd=WORKSPACE_DIR, check=False)
        subprocess.run(["git", "push"], cwd=WORKSPACE_DIR, check=False)

    access_token = cfg.get("tiktok_access_token") or os.environ.get("TIKTOK_ACCESS_TOKEN")
    image_base_url = cfg.get("tiktok_verified_image_base_url", "").rstrip("/")
    if not access_token or not image_base_url:
        raise ValueError(
            "config.json に 'tiktok_access_token' と 'tiktok_verified_image_base_url' を設定してください。"
        )

    photo_urls = [f"{image_base_url}/{ep_id}/0{i}_v5.jpg" for i in range(1, 6)]

    # GitHub Pages の反映完了を確認してから TikTok API を叩く（最大45秒待機）
    import time
    for attempt in range(15):
        try:
            req_check = urllib.request.Request(photo_urls[0], method="HEAD")
            with urllib.request.urlopen(req_check, timeout=5) as r:
                if r.status == 200:
                    break
        except Exception:
            if attempt == 0:
                print("[GitHub Pages] 公開反映を待機中...")
            time.sleep(3)

    payload = {
        "post_info": {
            "title": ep["tiktok"]["title"][:90],
            "description": ep["tiktok"]["caption"],
        },
        "source_info": {
            "source": "PULL_FROM_URL",
            "photo_cover_index": 0,
            "photo_images": photo_urls,
        },
        "post_mode": "MEDIA_UPLOAD",  # スマホのTikTokアプリの通知（下書き）へ飛ばし、アプリ側でBGMを付けて投稿可能
        "media_type": "PHOTO",
    }

    def _send(token: str) -> str:
        req = urllib.request.Request(
            "https://open.tiktokapis.com/v2/post/publish/content/init/",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=UTF-8",
            },
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")

    try:
        body = _send(access_token)
    except urllib.error.HTTPError as e:
        if e.code == 401 and cfg.get("tiktok_refresh_token"):
            print("[TikTok Official API] トークン期限切れのため自動更新します...")
            access_token = refresh_tiktok_token(cfg)
            body = _send(access_token)
        else:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"TikTok API エラー ({e.code}): {err_body}") from e

    print(f"[TikTok Official API] 送信完了！スマホのTikTokアプリの通知（システム通知）を確認してください:\n{body}")


def refresh_tiktok_token(cfg: dict) -> str:
    """refresh_token を使って新しい access_token を自動取得し config.json を更新する。"""
    token_data = urllib.parse.urlencode(
        {
            "client_key": cfg["tiktok_client_key"],
            "client_secret": cfg["tiktok_client_secret"],
            "grant_type": "refresh_token",
            "refresh_token": cfg["tiktok_refresh_token"],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://open.tiktokapis.com/v2/oauth/token/",
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        res_json = json.loads(resp.read().decode("utf-8"))
        if "access_token" in res_json:
            cfg["tiktok_access_token"] = res_json["access_token"]
            if "refresh_token" in res_json:
                cfg["tiktok_refresh_token"] = res_json["refresh_token"]
            save_config(cfg)
            return cfg["tiktok_access_token"]
        raise RuntimeError(f"トークン更新エラー: {res_json}")


def exchange_code_for_token(cfg: dict, code_or_url: str) -> None:
    """認可コード（またはリダイレクト先URL全体）から access_token と refresh_token を取得して保存する。"""
    client_key = cfg.get("tiktok_client_key")
    client_secret = cfg.get("tiktok_client_secret")
    redirect_uri = cfg.get("tiktok_redirect_uri", "https://example.com/callback")

    code = code_or_url.strip()
    if "code=" in code:
        parsed = urllib.parse.urlparse(code)
        qs = urllib.parse.parse_qs(parsed.query)
        code = qs.get("code", [code])[0]
    code = urllib.parse.unquote(code)

    token_data = urllib.parse.urlencode(
        {
            "client_key": client_key,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://open.tiktokapis.com/v2/oauth/token/",
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        res_json = json.loads(resp.read().decode("utf-8"))
        if "access_token" in res_json:
            cfg["tiktok_access_token"] = res_json.get("access_token")
            cfg["tiktok_refresh_token"] = res_json.get("refresh_token")
            save_config(cfg)
            print("[OK] access_token と refresh_token を config.json に保存しました！")
        else:
            print("[エラー] トークン取得レスポンス:", res_json)


def main() -> None:
    parser = argparse.ArgumentParser(description="TikTok 1000年後の名言 下書き自動アップローダー")
    parser.add_argument("--id", help="送信する記録番号（例: 005）")
    parser.add_argument("--code", help="OAuth認証後のリダイレクト先URLまたはcodeを渡してトークンを保存")
    args = parser.parse_args()

    cfg = load_config()
    if args.code:
        exchange_code_for_token(cfg, args.code)
        return

    if not args.id:
        print("エラー: --id 005 のように記録番号を指定してください。")
        sys.exit(1)

    episodes = json.loads((WORKSPACE_DIR / "episodes.json").read_text(encoding="utf-8"))
    ep = next((e for e in episodes if e["id"] == args.id), None)
    if not ep:
        print(f"記録番号 {args.id} が episodes.json に見つかりません。")
        sys.exit(1)

    post_dir = WORKSPACE_DIR / "posts" / f"{ep['id']}_{ep['theme']}"
    provider = cfg.get("provider", "tiktok_official")
    if provider == "tiktok_official":
        upload_via_tiktok_official_api(ep, cfg)
    else:
        upload_via_upload_post(ep, post_dir, cfg)


if __name__ == "__main__":
    main()
