"""Publish a post or story to Instagram (@paper.lessons) through the Graph API.

    uv run python scripts/marketing/ig_publish.py marketing/instagram/posts/03-a-real-page --dry-run
    uv run python scripts/marketing/ig_publish.py marketing/instagram/posts/03-a-real-page
    uv run python scripts/marketing/ig_publish.py marketing/instagram/stories/highlights/levels.png --story
    uv run python scripts/marketing/ig_publish.py --check       # token + account + quota, posts nothing
    uv run python scripts/marketing/ig_publish.py --inbox       # comments on recent posts + DMs
    uv run python scripts/marketing/ig_publish.py --reply-comment <comment id> "Thank you!"
    uv run python scripts/marketing/ig_publish.py --reply-dm <user id> "Hi! ..."   # within 24h of their message

Every publish is appended to marketing/instagram/posted.jsonl; a folder that's already in it is refused
unless --force. Full guide: marketing/instagram/API.md.

A post folder holds `caption.md` (an `Images:` line listing the files in order, `## Caption` and
`## Alt text` sections, as written by instagram_launch.py). One image → single post, several → carousel.

Instagram only takes media by public URL, so each image is converted to JPEG (macOS `sips`), uploaded
to R2 as `social/<content hash>.jpg` with wrangler, and served by the site at
https://paperlessons.com/media/social/<hash>.jpg (apps/web/worker/index.ts).

Needs in the repo-root `.env` (git-ignored): IG_ACCESS_TOKEN, IG_USER_ID. The token is a short-lived
Facebook-style token (EAA…) from the Postman app's dashboard; regenerate it there when it expires.
It works on graph.facebook.com only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GRAPH = "https://graph.facebook.com/v23.0"
MEDIA_BASE = "https://paperlessons.com/media/social"
BUCKET = "paperlessons-files"
# Cloudflare's bot filter on paperlessons.com rejects Python's default user agent.
UA = {"User-Agent": "paperlessons-publisher/1.0"}


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    for key in ("IG_ACCESS_TOKEN", "IG_USER_ID"):
        if not env.get(key):
            sys.exit(f"{key} is missing from {path}")
    return env


class GraphError(RuntimeError):
    pass


def graph(method: str, path: str, token: str, **params: str) -> dict:
    """Call the Graph API. The token goes in the body (POST) or query (GET), never in error output."""
    params = {k: v for k, v in params.items() if v is not None}
    params["access_token"] = token
    data = urllib.parse.urlencode(params).encode()
    url = f"{GRAPH}/{path}"
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data.decode()}")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            err = json.loads(body).get("error", {})
            msg = err.get("error_user_msg") or err.get("message") or body
            code = err.get("code")
        except json.JSONDecodeError:
            msg, code = body, None
        if code == 190:
            msg += " (the token has expired or is wrong: regenerate it in the Postman app and update .env)"
        raise GraphError(f"{method} {path}: {msg}") from None


# ---------------------------------------------------------------- reading a post folder


def section(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else ""


def read_post(folder: Path) -> tuple[list[Path], str, str]:
    md = (folder / "caption.md").read_text()
    m = re.search(r"^Images:\s*(.+)$", md, re.M)
    if not m:
        sys.exit(f"{folder}/caption.md has no 'Images:' line")
    images = [folder / name for name in re.findall(r"`([^`]+)`", m.group(1))]
    for img in images:
        if not img.exists():
            sys.exit(f"missing image {img}")
    caption = section(md, "Caption")
    if not caption:
        sys.exit(f"{folder}/caption.md has no '## Caption' section")
    return images, caption, section(md, "Alt text")


# ---------------------------------------------------------------- hosting


def to_jpeg(src: Path, tmp: Path) -> Path:
    if src.suffix.lower() in (".jpg", ".jpeg"):
        return src
    out = tmp / (src.stem + ".jpg")
    subprocess.run(
        ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "95", str(src), "--out", str(out)],
        check=True, capture_output=True,
    )
    return out


def host(src: Path, tmp: Path, dry_run: bool) -> str:
    jpg = to_jpeg(src, tmp)
    name = hashlib.sha256(jpg.read_bytes()).hexdigest()[:16] + ".jpg"
    url = f"{MEDIA_BASE}/{name}"
    if dry_run:
        return url
    # Skip the upload when the site already serves this exact file.
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD", headers=UA), timeout=20):
            return url
    except urllib.error.URLError:
        pass
    subprocess.run(
        ["npx", "wrangler", "r2", "object", "put", f"{BUCKET}/social/{name}", "--file", str(jpg),
         "--content-type", "image/jpeg", "--remote"],
        cwd=ROOT / "apps" / "web", check=True, capture_output=True,
    )
    with urllib.request.urlopen(urllib.request.Request(url, method="HEAD", headers=UA), timeout=20) as resp:
        if resp.status != 200:
            sys.exit(f"uploaded {name} but {url} answers {resp.status}")
    return url


# ---------------------------------------------------------------- publishing


def wait_ready(container: str, token: str) -> None:
    for _ in range(30):
        status = graph("GET", container, token, fields="status_code,status").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise GraphError(f"container {container} is {status}")
        time.sleep(2)
    raise GraphError(f"container {container} not ready after 60s")


def create_image(ig: str, token: str, url: str, **extra: str) -> str:
    """Create an image container; retry without alt_text if this API version doesn't take it."""
    try:
        return graph("POST", f"{ig}/media", token, image_url=url, **extra)["id"]
    except GraphError as e:
        if extra.get("alt_text") and "alt_text" in str(e):
            extra.pop("alt_text")
            print("  (alt text not accepted by the API; posting without it)")
            return graph("POST", f"{ig}/media", token, image_url=url, **extra)["id"]
        raise


def slide_alts(alt: str, n: int) -> list[str]:
    """Split carousel alt text written as "Slide 1: ..." paragraphs into one alt per slide (else repeat it)."""
    parts = dict(re.findall(r"^Slide (\d+):\s*(.+?)(?=^Slide \d+:|\Z)", alt, re.S | re.M))
    if len(parts) == n and all(str(i) in parts for i in range(1, n + 1)):
        return [" ".join(parts[str(i)].split()) for i in range(1, n + 1)]
    return [alt] * n


def publish(ig: str, token: str, urls: list[str], caption: str, alt: str, story: bool) -> dict:
    if story:
        container = create_image(ig, token, urls[0], media_type="STORIES")
    elif len(urls) == 1:
        container = create_image(ig, token, urls[0], caption=caption, alt_text=alt or None)
    else:
        children = []
        for url, child_alt in zip(urls, slide_alts(alt, len(urls))):
            child = create_image(ig, token, url, is_carousel_item="true", alt_text=child_alt or None)
            wait_ready(child, token)
            children.append(child)
        container = graph("POST", f"{ig}/media", token, media_type="CAROUSEL",
                          children=",".join(children), caption=caption)["id"]
    wait_ready(container, token)
    media_id = graph("POST", f"{ig}/media_publish", token, creation_id=container)["id"]
    return graph("GET", media_id, token, fields="id,media_type,permalink,timestamp")


def check(ig: str, token: str) -> None:
    acct = graph("GET", ig, token, fields="username,name,media_count,followers_count")
    quota = graph("GET", f"{ig}/content_publishing_limit", token, fields="config,quota_usage")["data"][0]
    print(f"@{acct['username']} ({acct['name']}): {acct['media_count']} posts, "
          f"{acct.get('followers_count', 0)} followers")
    print(f"published in the last 24h: {quota['quota_usage']} of {quota['config']['quota_total']}")


LOG = ROOT / "marketing" / "instagram" / "posted.jsonl"


def log_key(target: Path, story: bool) -> str:
    try:
        rel = str(target.resolve().relative_to(ROOT))
    except ValueError:
        rel = str(target.resolve())
    return ("story:" if story else "post:") + rel


def read_log() -> list[dict]:
    if not LOG.exists():
        return []
    return [json.loads(line) for line in LOG.read_text().splitlines() if line.strip()]


def write_log(entry: dict) -> None:
    with LOG.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- comments and messages


def inbox(ig: str, token: str, posts: int) -> None:
    """New comments on the latest posts, then DM conversations with their latest messages."""
    media = graph("GET", f"{ig}/media", token, fields="id,caption,permalink,comments_count", limit=str(posts))["data"]
    print(f"COMMENTS (latest {len(media)} posts)")
    any_comment = False
    for m in media:
        if not m.get("comments_count"):
            continue
        title = (m.get("caption") or "").splitlines()[0][:50]
        print(f"\n  {title} — {m['permalink']}")
        comments = graph("GET", f"{m['id']}/comments", token,
                         fields="id,text,username,timestamp,hidden,replies{id,text,username,timestamp}")["data"]
        for c in comments:
            any_comment = True
            hidden = " [hidden]" if c.get("hidden") else ""
            print(f"    [{c['id']}] @{c.get('username', '?')} {c['timestamp'][:16]}{hidden}: {c['text']}")
            for r in (c.get("replies") or {}).get("data", []):
                print(f"        ↳ @{r.get('username', '?')}: {r['text']}")
    if not any_comment:
        print("  no comments")

    print("\nMESSAGES")
    try:
        convs = graph("GET", f"{ig}/conversations", token, platform="instagram",
                      fields="id,updated_time,participants,messages.limit(3){id,message,from,created_time}")["data"]
    except GraphError as e:
        print(f"  can't read messages: {e}")
        print("  (Instagram app → Settings → Messages and story replies → Message controls → Connected tools →"
              " Allow access to messages)")
        return
    if not convs:
        print("  no conversations (if you know there are some, turn on 'Allow access to messages', see API.md)")
    for c in convs:
        people = [p for p in c.get("participants", {}).get("data", []) if p.get("id") != ig]
        who = ", ".join(f"@{p.get('username', '?')} (id {p.get('id')})" for p in people)
        print(f"\n  {who} — updated {c.get('updated_time', '')[:16]}")
        for msg in reversed(c.get("messages", {}).get("data", [])):
            sender = msg.get("from", {}).get("username", "?")
            print(f"    {msg.get('created_time', '')[:16]} @{sender}: {msg.get('message', '(attachment)')}")


def reply_comment(comment_id: str, text: str, token: str) -> None:
    r = graph("POST", f"{comment_id}/replies", token, message=text)
    print(f"replied to comment {comment_id}: reply {r['id']}")


def hide_comment(comment_id: str, token: str) -> None:
    graph("POST", comment_id, token, hide="true")
    print(f"hid comment {comment_id}")


def reply_dm(ig: str, recipient: str, text: str, token: str) -> None:
    """Meta only allows this within 24 hours of the person's last message."""
    r = graph("POST", f"{ig}/messages", token, recipient=json.dumps({"id": recipient}),
              message=json.dumps({"text": text}))
    print(f"sent message {r.get('message_id', r)} to {recipient}")


# ---------------------------------------------------------------- main


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", help="post folder (with caption.md) or an image for --story")
    ap.add_argument("--story", action="store_true", help="publish one image as a story (no caption)")
    ap.add_argument("--dry-run", action="store_true", help="show what would be posted; upload and post nothing")
    ap.add_argument("--force", action="store_true", help="post again even if posted.jsonl says it's already up")
    ap.add_argument("--check", action="store_true", help="check token, account and quota, then stop")
    ap.add_argument("--inbox", action="store_true", help="list comments on recent posts and DM conversations")
    ap.add_argument("--posts", type=int, default=12, help="with --inbox: how many recent posts to scan")
    ap.add_argument("--reply-comment", nargs=2, metavar=("COMMENT_ID", "TEXT"), help="reply to a comment (public)")
    ap.add_argument("--hide-comment", metavar="COMMENT_ID", help="hide a comment (spam, rude)")
    ap.add_argument("--reply-dm", nargs=2, metavar=("USER_ID", "TEXT"), help="send a DM (within 24h of theirs)")
    args = ap.parse_args()

    env = load_env()
    token, ig = env["IG_ACCESS_TOKEN"], env["IG_USER_ID"]
    try:
        if args.inbox:
            inbox(ig, token, args.posts)
            return
        if args.reply_comment:
            reply_comment(*args.reply_comment, token)
            return
        if args.hide_comment:
            hide_comment(args.hide_comment, token)
            return
        if args.reply_dm:
            reply_dm(ig, *args.reply_dm, token)
            return
        if args.check or not args.target:
            check(ig, token)
            return
        target = Path(args.target)
        key = log_key(target, args.story)
        done = [e for e in read_log() if e["key"] == key]
        if done and not args.force and not args.dry_run:
            sys.exit(f"already posted {done[-1]['posted_at']}: {done[-1].get('permalink')} (use --force to post again)")
        if args.story:
            images = sorted(target.glob("*.png")) if target.is_dir() else [target]
            if len(images) != 1:
                sys.exit("--story takes exactly one image")
            caption = alt = ""
        else:
            if not target.is_dir():
                sys.exit("a feed post is a folder with caption.md (use --story for a single image)")
            images, caption, alt = read_post(target)
            if len(images) > 10:
                sys.exit("a carousel takes at most 10 images")

        with tempfile.TemporaryDirectory() as tmp:
            urls = [host(img, Path(tmp), args.dry_run) for img in images]
        kind = "story" if args.story else ("carousel" if len(urls) > 1 else "image post")
        print(f"{kind}: {len(urls)} image(s)")
        for img, url in zip(images, urls):
            print(f"  {img} → {url}")
        if caption:
            print(f"caption ({len(caption)} chars): {caption.splitlines()[0]} …")
        if alt:
            print(f"alt text: {alt[:80]}…")
        if args.dry_run:
            check(ig, token)
            print("dry run: nothing uploaded or posted")
            return
        result = publish(ig, token, urls, caption, alt, args.story)
        write_log({"key": key, "kind": kind, "media_id": result["id"], "permalink": result.get("permalink"),
                   "posted_at": result.get("timestamp"), "images": urls})
        print(f"published {result['media_type']} {result['id']} at {result['timestamp']}")
        if result.get("permalink"):
            print(result["permalink"])
    except GraphError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
