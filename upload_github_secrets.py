#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, "/tmp/pynacl")
from nacl import encoding, public

WORKSPACE_DIR = Path(__file__).resolve().parent
cfg = json.loads((WORKSPACE_DIR / "config.json").read_text(encoding="utf-8"))

GITHUB_TOKEN = sys.argv[1]
REPO = "miracle-tamechan0429-ops/quotes3000"

# 1. Fetch public key
req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",
    headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    },
)
with urllib.request.urlopen(req) as resp:
    pk_data = json.loads(resp.read().decode("utf-8"))

key_id = pk_data["key_id"]
pub_key = public.PublicKey(pk_data["key"].encode("utf-8"), encoding.Base64Encoder())
sealed_box = public.SealedBox(pub_key)

secrets_to_upload = {
    "TIKTOK_CLIENT_KEY": cfg["tiktok_client_key"],
    "TIKTOK_CLIENT_SECRET": cfg["tiktok_client_secret"],
    "TIKTOK_ACCESS_TOKEN": cfg["tiktok_access_token"],
    "TIKTOK_REFRESH_TOKEN": cfg["tiktok_refresh_token"],
    "GH_PAT": GITHUB_TOKEN,
}

for name, val in secrets_to_upload.items():
    encrypted = base64.b64encode(sealed_box.encrypt(val.encode("utf-8"))).decode("utf-8")
    body = json.dumps({"encrypted_value": encrypted, "key_id": key_id}).encode("utf-8")
    put_req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/actions/secrets/{name}",
        data=body,
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
        method="PUT",
    )
    with urllib.request.urlopen(put_req) as r:
        print(f"✅ Uploaded GitHub Secret: {name} (HTTP {r.status})")
