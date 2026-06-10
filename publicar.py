#!/usr/bin/env python3
"""
publicar.py — Puja index.html actualitzat a GitHub Pages
=========================================================
Ús:
    python3 publicar.py

Configura GITHUB_TOKEN i GITHUB_REPO abans d'executar.
"""

import base64, json, os, sys
import requests

# ── CONFIG ── canvia si cal ───────────────────────────────────────────────────
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")   # o posa'l directament
GITHUB_REPO  = "IsabelCasanova/barcelona-projectes"
FILE_PATH    = "index.html"
LOCAL_FILE   = "index.html"
BRANCH       = "main"
COMMIT_MSG   = "Actualització mensual de dades"
# ─────────────────────────────────────────────────────────────────────────────

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/vnd.github.v3+json",
}
BASE = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"

def get_current_sha():
    r = requests.get(BASE, headers=HEADERS)
    if r.status_code == 200:
        return r.json().get("sha")
    return None

def upload(local_path):
    if not GITHUB_TOKEN:
        print("❌ Falta GITHUB_TOKEN. Configura'l al script o com a variable d'entorn.")
        sys.exit(1)

    if not os.path.exists(local_path):
        print(f"❌ No trobo el fitxer: {local_path}")
        sys.exit(1)

    with open(local_path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf-8")

    sha = get_current_sha()
    payload = {
        "message": COMMIT_MSG,
        "content": content,
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(BASE, headers=HEADERS, json=payload)
    if r.status_code in (200, 201):
        url = f"https://{GITHUB_REPO.split('/')[0].lower()}.github.io/barcelona-projectes/"
        print(f"✅ Publicat correctament!")
        print(f"🌐 URL: {url}")
    else:
        print(f"❌ Error {r.status_code}: {r.json().get('message', r.text)}")

if __name__ == "__main__":
    print(f"📤 Pujant {LOCAL_FILE} a {GITHUB_REPO}…")
    upload(LOCAL_FILE)
