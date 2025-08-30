#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make line-by-line commits to a GitHub repository via the Contents API.
Supports fixed or random delays (e.g., 60, 60-120, 1m-2m, 500ms-2s).
"""

import os, sys, json, time, base64, argparse, urllib.request, urllib.error, urllib.parse
import random, re

GITHUB_API = "https://api.github.com"
API_VERSION = "2022-11-28"

# --- HTTP helpers -----------------------------------------------------------------------------

def http_request(method, url, token, data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", API_VERSION)
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=body) as r:
            return r.getcode(), json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            payload = e.read().decode("utf-8")
            return e.code, json.loads(payload) if payload else {"message": str(e)}
        except Exception:
            return e.code, {"message": str(e)}

# --- GitHub Contents API helpers --------------------------------------------------------------

def get_file(owner, repo, path, branch, token):
    """Return (text, sha) if the file exists, or (None, None) if it does not."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{urllib.parse.quote(path)}?ref={urllib.parse.quote(branch)}"
    code, resp = http_request("GET", url, token)
    if code == 200 and isinstance(resp, dict) and "content" in resp:
        encoding = resp.get("encoding", "base64")
        if encoding != "base64":
            raise RuntimeError(f"Unexpected content encoding: {encoding}")
        content_b64 = resp["content"]
        text = base64.b64decode("".join(content_b64.splitlines())).decode("utf-8", errors="replace")
        return text, resp.get("sha")
    if code == 404:
        return None, None
    raise RuntimeError(f"GET contents failed: HTTP {code} {resp}")

def put_file(owner, repo, path, branch, message, text, token, sha=None, committer_name=None, committer_email=None):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{urllib.parse.quote(path)}"
    b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
    payload = {"message": message, "content": b64, "branch": branch}
    if sha:
        payload["sha"] = sha
    if committer_name and committer_email:
        payload["committer"] = {"name": committer_name, "email": committer_email}
    return http_request("PUT", url, token, payload)

# --- Utility ----------------------------------------------------------------------------------

def shorten(s, n=60):
    s = s.strip().replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"

_DURATION_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(ms|s|m|h)?\s*$", re.IGNORECASE)

def parse_duration(token: str) -> float:
    m = _DURATION_RE.match(token)
    if not m:
        raise ValueError(f"Invalid duration: {token!r}")
    value = float(m.group(1))
    unit = (m.group(2) or "s").lower()
    factor = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}[unit]
    return value * factor

def build_delay_getter(spec: str):
    if "-" in spec:
        left, right = spec.split("-", 1)
        a, b = parse_duration(left), parse_duration(right)
        lo, hi = (a, b) if a <= b else (b, a)
        lo = max(0.0, lo)
        def next_delay():
            return random.uniform(lo, hi)
        return next_delay, f"{lo:.3f}-{hi:.3f}s"
    else:
        fixed = parse_duration(spec)
        fixed = max(0.0, fixed)
        def next_delay():
            return fixed
        return next_delay, f"{fixed:.3f}s"

# --- Main -------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Line-by-line commits to GitHub with delay (range supported)")
    ap.add_argument("--token", help="GitHub Personal Access Token (or environment variable GITHUB_TOKEN)")
    ap.add_argument("--repo", required=True, help="owner/repo (e.g., yourname/yourrepo)")
    ap.add_argument("--path", required=True, help="File path in the repository (e.g., logs/notes.txt)")
    ap.add_argument("--branch", default="main", help="Branch name (default: main)")
    ap.add_argument("--text", help="Input text (will be split by lines)")
    ap.add_argument("--text-file", help="Path to a local text file (alternative to --text)")
    ap.add_argument("--delay", default="60", help="Pause or range (e.g., 60, 60-120, 1m-2m, 500ms-2s). Default 60s")
    ap.add_argument("--skip-empty", action="store_true", help="Skip empty lines")
    ap.add_argument("--start-index", type=int, default=0, help="Start from line with this index (0-based)")
    ap.add_argument("--commit-prefix", default="chore: append line", help="Commit message prefix")
    ap.add_argument("--committer-name", help="Committer name (optional)")
    ap.add_argument("--committer-email", help="Committer email (optional)")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be committed without pushing")
    args = ap.parse_args()

    token = args.token or os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ Error: provide --token or set GITHUB_TOKEN env var", file=sys.stderr)
        sys.exit(2)

    if "/" not in args.repo:
        print("❌ Error: --repo must be in form owner/repo", file=sys.stderr)
        sys.exit(2)
    owner, repo = args.repo.split("/", 1)

    try:
        next_delay, delay_descr = build_delay_getter(str(args.delay))
    except Exception as e:
        print(f"⚠️ Invalid --delay: {e}", file=sys.stderr)
        sys.exit(2)

    if args.text is not None:
        raw = args.text
    elif args.text_file:
        with open(args.text_file, "r", encoding="utf-8") as f:
            raw = f.read()
    else:
        if sys.stdin.isatty():
            print("⌨️ Paste text and finish input: Ctrl+D (macOS/Linux) or Ctrl+Z Enter (Windows).", file=sys.stderr)
        raw = sys.stdin.read()

    lines = raw.splitlines()
    if args.skip_empty:
        lines = [ln for ln in lines if ln.strip() != ""]
    if args.start_index > 0:
        lines = lines[args.start_index:]

    if not lines:
        print("⚠️ No lines to commit.", file=sys.stderr)
        sys.exit(0)

    try:
        current_text, file_sha = get_file(owner, repo, args.path, args.branch, token)
    except Exception as e:
        print(f"❌ Failed to fetch file: {e}", file=sys.stderr)
        sys.exit(1)

    if current_text is None:
        current_text = ""
        file_sha = None
        print(f"📄 File {args.path} does not exist — it will be created.", file=sys.stderr)
    else:
        print(f"📄 File {args.path} found — appending.", file=sys.stderr)

    print(f"⏱️ Delay mode: {delay_descr}", file=sys.stderr)

    total = len(lines)
    committed = 0
    try:
        for idx, line in enumerate(lines, 1):
            if current_text and not current_text.endswith("\n"):
                current_text += "\n"
            current_text += line + "\n"

            msg = f"{args.commit_prefix} {idx}/{total}: {shorten(line)}"

            if args.dry_run:
                print(f"📝 [DRY-RUN] {msg}")
            else:
                code, resp = put_file(
                    owner, repo, args.path, args.branch, msg, current_text,
                    token, sha=file_sha,
                    committer_name=args.committer_name, committer_email=args.committer_email
                )
                if code not in (200, 201):
                    print(f"❌ Commit error (HTTP {code}): {resp.get('message')}", file=sys.stderr)
                    if "errors" in resp:
                        print(json.dumps(resp["errors"], ensure_ascii=False, indent=2), file=sys.stderr)
                    sys.exit(1)

                new_content = resp.get("content") or {}
                file_sha = new_content.get("sha", file_sha)
                commit_sha = (resp.get("commit") or {}).get("sha")
                html_url = new_content.get("html_url")
                committed += 1
                print(f"✅ Commit {committed}/{total}: {commit_sha or '(sha not returned)'}  {html_url or ''}")

                if idx < total:
                    delay_sec = max(0.0, float(next_delay()))
                    print(f"⏳ Pause: {delay_sec:.2f} s", file=sys.stderr)
                    time.sleep(delay_sec)

        if args.dry_run:
            print("🔍 DRY-RUN finished. Nothing was pushed.")
        else:
            print(f"🎉 Done. Made {committed} commit(s).")
    except KeyboardInterrupt:
        print("\n⛔ Interrupted by user. Already-pushed commits remain in the repository.", file=sys.stderr)
        sys.exit(130)

if __name__ == "__main__":
    main()