#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
『1000年後の名言』 クラウド＆スリープ復帰対応・毎朝9時自動送信スクリプト (cloud_send_daily.py)
- Python標準ライブラリのみで動作（GitHub Actionsクラウド上でもMacローカルでも実行可能）
- 日本時間 (JST: UTC+9) の日付で「1日1回」を厳密管理（クラウドとMacの二重送信を防止）
- TikTok公式APIのトークンを自動リフレッシュして MEDIA_UPLOAD（スマホのTikTok通知/下書き）へ送信
- 送信後、スマホ用1タップコピー帳 (docs/index.html) の最上部に「🔥本日送信分」として1コメ目＆キャプションをハイライト更新
"""

import argparse
import datetime
import html
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = WORKSPACE_DIR / "config.json"
EPISODES_PATH = WORKSPACE_DIR / "episodes.json"
LAST_SENT_PATH = WORKSPACE_DIR / ".last_sent_date"
DOCS_INDEX_PATH = WORKSPACE_DIR / "docs" / "index.html"
LATEST_COMMENT_PATH = WORKSPACE_DIR / "LATEST_FIRST_COMMENT.txt"

JST = datetime.timezone(datetime.timedelta(hours=9))


def get_today_jst() -> str:
    return datetime.datetime.now(JST).date().isoformat()


def load_credentials() -> dict:
    cfg = {}
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}
    return {
        "client_key": os.environ.get("TIKTOK_CLIENT_KEY") or cfg.get("tiktok_client_key", ""),
        "client_secret": os.environ.get("TIKTOK_CLIENT_SECRET") or cfg.get("tiktok_client_secret", ""),
        "access_token": os.environ.get("TIKTOK_ACCESS_TOKEN") or cfg.get("tiktok_access_token", ""),
        "refresh_token": os.environ.get("TIKTOK_REFRESH_TOKEN") or cfg.get("tiktok_refresh_token", ""),
        "image_base_url": (
            os.environ.get("TIKTOK_VERIFIED_IMAGE_BASE_URL")
            or cfg.get("tiktok_verified_image_base_url", "https://miracle-tamechan0429-ops.github.io/quotes3000/posts")
        ).rstrip("/"),
        "_raw_cfg": cfg,
    }


def refresh_access_token(creds: dict) -> str:
    data = urllib.parse.urlencode(
        {
            "client_key": creds["client_key"],
            "client_secret": creds["client_secret"],
            "grant_type": "refresh_token",
            "refresh_token": creds["refresh_token"],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://open.tiktokapis.com/v2/oauth/token/",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        res_json = json.loads(resp.read().decode("utf-8"))
    if "access_token" not in res_json:
        raise RuntimeError(f"TikTok token refresh failed: {res_json}")

    new_access = res_json["access_token"]
    new_refresh = res_json.get("refresh_token", creds["refresh_token"])
    creds["access_token"] = new_access
    creds["refresh_token"] = new_refresh

    if CONFIG_PATH.exists() and creds.get("_raw_cfg"):
        raw = creds["_raw_cfg"]
        raw["tiktok_access_token"] = new_access
        raw["tiktok_refresh_token"] = new_refresh
        CONFIG_PATH.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

    # GitHub Actions 上で動いている場合、最新のトークンを GitHub Secrets にも自動保存（半永久稼働用）
    gh_pat = os.environ.get("GH_PAT")
    if gh_pat:
        try:
            import base64
            from nacl import encoding, public
            repo = "miracle-tamechan0429-ops/quotes3000"
            pk_req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
                headers={"Authorization": f"token {gh_pat}", "Accept": "application/vnd.github+json"},
            )
            with urllib.request.urlopen(pk_req, timeout=15) as r:
                pk_data = json.loads(r.read().decode("utf-8"))
            sealed_box = public.SealedBox(
                public.PublicKey(pk_data["key"].encode("utf-8"), encoding.Base64Encoder())
            )
            for s_name, s_val in [("TIKTOK_ACCESS_TOKEN", new_access), ("TIKTOK_REFRESH_TOKEN", new_refresh)]:
                enc_val = base64.b64encode(sealed_box.encrypt(s_val.encode("utf-8"))).decode("utf-8")
                put_req = urllib.request.Request(
                    f"https://api.github.com/repos/{repo}/actions/secrets/{s_name}",
                    data=json.dumps({"encrypted_value": enc_val, "key_id": pk_data["key_id"]}).encode("utf-8"),
                    headers={
                        "Authorization": f"token {gh_pat}",
                        "Accept": "application/vnd.github+json",
                        "Content-Type": "application/json",
                    },
                    method="PUT",
                )
                urllib.request.urlopen(put_req, timeout=15).close()
        except Exception as e:
            print(f"[WARN] Could not self-update GitHub Secrets: {e}")

    return new_access


def send_tiktok_draft(ep: dict, creds: dict) -> str:
    ep_id = ep["id"]
    photo_urls = [f"{creds['image_base_url']}/{ep_id}/0{i}_v5.jpg" for i in range(1, 6)]
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
        "post_mode": "MEDIA_UPLOAD",
        "media_type": "PHOTO",
    }

    def _call(token: str) -> str:
        req = urllib.request.Request(
            "https://open.tiktokapis.com/v2/post/publish/content/init/",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=UTF-8",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")

    # 常に最新のトークンへリフレッシュを試みる（有効期限切れ防止）
    token = creds["access_token"]
    if creds.get("refresh_token") and creds.get("client_key") and creds.get("client_secret"):
        try:
            token = refresh_access_token(creds)
        except Exception as e:
            print(f"[WARN] Token pre-refresh skipped: {e}")

    try:
        return _call(token)
    except urllib.error.HTTPError as e:
        if e.code == 401 and creds.get("refresh_token"):
            token = refresh_access_token(creds)
            return _call(token)
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"TikTok API Error ({e.code}): {err_body}") from e


def update_docs_index(episodes: list, latest_ep: dict, today_jst: str) -> None:
    def render_card(ep: dict, is_highlight: bool = False) -> str:
        eid = ep["id"]
        theme = html.escape(ep["theme"])
        quote_arr = ep["slide4"].get("quote_lines") or ep["slide4"].get("quote", [])
        quote = html.escape(" / ".join(quote_arr))
        comment_raw = ep["tiktok"]["comment"]
        caption_raw = f"{ep['tiktok']['title']}\n\n{ep['tiktok']['caption']}"
        comment_js = json.dumps(comment_raw, ensure_ascii=False)
        caption_js = json.dumps(caption_raw, ensure_ascii=False)
        badge = (
            f'<div class="badge">🔥 本日（{today_jst} 朝9:00）TikTok下書き送信済み</div>'
            if is_highlight
            else ""
        )
        card_cls = "card highlight" if is_highlight else "card"
        return f"""
    <div class="{card_cls}">
      {badge}
      <div class="hdr">【記録番号：{eid}】{theme}</div>
      <div class="quote">{quote}</div>
      <div class="btns">
        <button onclick='copyText({comment_js}, this, "✅ 1コメ目をコピーしました！")' class="btn primary">💬 1コメ目をコピー</button>
        <button onclick='copyText({caption_js}, this, "✅ キャプションをコピーしました！")' class="btn">📋 キャプションをコピー</button>
      </div>
      <details {"open" if is_highlight else ""}>
        <summary>テキスト全文を表示</summary>
        <pre>{html.escape(comment_raw)}</pre>
        <pre>{html.escape(caption_raw)}</pre>
      </details>
    </div>"""

    cards_html = []
    if latest_ep:
        cards_html.append(render_card(latest_ep, is_highlight=True))

    for ep in episodes:
        if int(ep["id"]) >= 5 and (not latest_ep or ep["id"] != latest_ep["id"]):
            cards_html.append(render_card(ep, is_highlight=False))

    page_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>1000年後の名言｜スマホ1タップコピー帳</title>
<style>
  body {{ background:#0d0f12; color:#f2efe9; font-family:-apple-system,BlinkMacSystemFont,"Hiragino Mincho ProN",serif; margin:0; padding:16px; }}
  h1 {{ font-size:20px; text-align:center; color:#f8d480; margin:8px 0 20px; }}
  .card {{ background:#171a20; border:1px solid #2e3440; border-radius:12px; padding:16px; margin-bottom:16px; }}
  .card.highlight {{ background:#1f1c14; border:2px solid #f8d480; box-shadow:0 0 20px rgba(248,212,128,0.18); }}
  .badge {{ display:inline-block; background:#f8d480; color:#000; font-size:12px; font-weight:bold; padding:4px 10px; border-radius:99px; margin-bottom:8px; }}
  .hdr {{ font-size:17px; font-weight:bold; color:#fff; margin-bottom:6px; }}
  .quote {{ font-size:14px; color:#f8d480; margin-bottom:14px; }}
  .btns {{ display:flex; gap:10px; flex-wrap:wrap; }}
  .btn {{ flex:1; min-width:140px; padding:12px; border-radius:8px; border:1px solid #444; background:#252a34; color:#fff; font-size:14px; font-weight:bold; cursor:pointer; }}
  .btn.primary {{ background:#b8862d; border-color:#f8d480; color:#000; }}
  details {{ margin-top:12px; font-size:13px; color:#ccc; }}
  pre {{ white-space:pre-wrap; background:#0d0f12; padding:10px; border-radius:6px; border:1px solid #222; }}
</style>
</head>
<body>
<h1>📕 1000年後の名言（スマホ1タップコピー帳）</h1>
{"".join(cards_html)}
<script>
function copyText(text, btn, msg) {{
  navigator.clipboard.writeText(text).then(function() {{
    var orig = btn.innerText;
    btn.innerText = msg;
    setTimeout(function() {{ btn.innerText = orig; }}, 2000);
  }});
}}
</script>
</body>
</html>
"""
    DOCS_INDEX_PATH.write_text(page_html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="同日送信済みでも強制送信（繰り上げ送信）する")
    parser.add_argument("--episode", type=str, default="", help="特定の記録番号（例: 006）を指定して即時送信し繰り上げる")
    parser.add_argument("--git-sync", action="store_true", help="実行前後に git pull / git push を行う")
    parser.add_argument("--after-9am", action="store_true", help="日本時間9:00以降のみ実行する（常駐デーモン用）")
    args = parser.parse_args()

    if args.episode:
        args.force = True

    now_jst = datetime.datetime.now(JST)
    if args.after_9am and not args.force and now_jst.hour < 9:
        sys.exit(0)

    today_jst = now_jst.date().isoformat()
    if not args.force and LAST_SENT_PATH.exists():
        last_sent = LAST_SENT_PATH.read_text(encoding="utf-8").strip()
        if last_sent == today_jst:
            print(f"[INFO] 本日（{today_jst} JST）分はすでに送信済みです（二重送信防止のためスキップ）。")
            sys.exit(0)

    if args.git_sync:
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=WORKSPACE_DIR, check=False)
        if not args.force and LAST_SENT_PATH.exists():
            if LAST_SENT_PATH.read_text(encoding="utf-8").strip() == today_jst:
                sys.exit(0)

    episodes = json.loads(EPISODES_PATH.read_text(encoding="utf-8"))
    if args.episode:
        ep_norm = args.episode.zfill(3)
        next_ep = next((e for e in episodes if e.get("id") == ep_norm), None)
    else:
        next_ep = next((e for e in episodes if e.get("status") == "ready"), None)
    if not next_ep:
        print("[INFO] 対象のエピソードが見つかりません。")
        sys.exit(0)

    creds = load_credentials()
    resp_body = send_tiktok_draft(next_ep, creds)
    print(f"[SUCCESS] TikTok API Response: {resp_body}")

    # ステータス更新
    next_ep["status"] = "published"
    next_ep["sent_date"] = today_jst
    EPISODES_PATH.write_text(json.dumps(episodes, ensure_ascii=False, indent=2), encoding="utf-8")
    LAST_SENT_PATH.write_text(today_jst, encoding="utf-8")

    # スマホ1タップコピー帳 (docs/index.html) を更新
    update_docs_index(episodes, next_ep, today_jst)

    # 最新ファーストコメントをファイル保存
    ep_id = next_ep["id"]
    theme = next_ep["theme"]
    comment_text = next_ep["tiktok"]["comment"]
    caption_text = f"{next_ep['tiktok']['title']}\n\n{next_ep['tiktok']['caption']}"
    summary_text = (
        f"【本日（{today_jst}）送信済み：記録番号 {ep_id}（{theme}）】\n\n"
        f"▼ ファーストコメント（1コメ目・意識調査）\n{comment_text}\n\n"
        f"▼ キャプション（説明文）\n{caption_text}\n"
    )
    LATEST_COMMENT_PATH.write_text(summary_text, encoding="utf-8")

    # Mac上で動いている場合はクリップボードコピー＆デスクトップ通知も行う
    if sys.platform == "darwin":
        try:
            subprocess.run(["pbcopy"], input=comment_text.encode("utf-8"), check=False)
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'display notification "【記録番号：{ep_id}】をTikTok下書きへ送信し、1コメ目をコピーしました！" with title "📕 1000年後の名言"',
                ],
                check=False,
            )
        except Exception:
            pass

    if args.git_sync:
        subprocess.run(
            ["git", "add", "episodes.json", ".last_sent_date", "docs/index.html", "LATEST_FIRST_COMMENT.txt"],
            cwd=WORKSPACE_DIR,
            check=False,
        )
        subprocess.run(
            ["git", "commit", "-m", f"Auto-send episode {ep_id} ({today_jst})"],
            cwd=WORKSPACE_DIR,
            check=False,
        )
        subprocess.run(["git", "push", "origin", "main"], cwd=WORKSPACE_DIR, check=False)

    print(f"\n==========================================")
    print(f"✅ 【記録番号：{ep_id}】（{theme}）をTikTok下書きへ送信しました！")
    print(f"==========================================\n")
    print(summary_text)


if __name__ == "__main__":
    main()
