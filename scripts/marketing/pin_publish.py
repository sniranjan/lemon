"""Publish pins to Pinterest (paperlessons.com) through the Pinterest API v5.

    uv run python scripts/marketing/pin_publish.py --dry-run --limit 3      # what would be sent; no network
    uv run python scripts/marketing/pin_publish.py --check                  # token works? (GET /v5/user_account)
    uv run python scripts/marketing/pin_publish.py --boards                 # list boards (saves their ids)
    uv run python scripts/marketing/pin_publish.py --boards --create        # create boards.yaml boards that are missing
    uv run python scripts/marketing/pin_publish.py --limit 3                # publish the next 3 unpinned pins
    uv run python scripts/marketing/pin_publish.py --only foxes-math        # publish one pin (if not pinned yet)
    uv run python scripts/marketing/pin_publish.py --refresh                # new access token from the refresh token

Pins come from a manifest written by pin_make.py (default marketing/pinterest/pins/manifest.json), in its order.
Every published pin is appended to marketing/pinterest/pinned.jsonl, keyed by (pin id, environment), so nothing
posts twice; sandbox pins never block production ones. Full guide: marketing/pinterest/README.md.

Pinterest takes the image by public URL: each PNG becomes a JPEG uploaded to R2 as social/<hash>.jpg and served at
https://paperlessons.com/media/social/<hash>.jpg (the same helper as ig_publish.py).

Needs PINTEREST_ACCESS_TOKEN in the environment or the repo-root `.env` (git-ignored). PINTEREST_SANDBOX=1 sends
everything to api-sandbox.pinterest.com (trial apps must) and uses PINTEREST_SANDBOX_TOKEN if it is set.
--dry-run needs no token and makes no network calls (only a local PNG → JPEG conversion to name the image URL).
The token is never printed.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ig_publish as P  # noqa: E402  (to_jpeg + host: PNG → JPEG → R2 → public URL)

ROOT = Path(__file__).resolve().parents[2]
PIN_DIR = ROOT / "marketing" / "pinterest"
MANIFEST = PIN_DIR / "pins" / "manifest.json"
BOARDS_YAML = PIN_DIR / "boards.yaml"
BOARD_IDS = PIN_DIR / "boards.json"  # {"production": {name: id}, "sandbox": {...}}: ids aren't secret
LOG = PIN_DIR / "pinned.jsonl"

API = {"production": "https://api.pinterest.com/v5", "sandbox": "https://api-sandbox.pinterest.com/v5"}
UA = P.UA["User-Agent"]

# Pinterest v5 PinCreate limits (api-description v5 openapi.yaml): title 100, description 800, alt_text 500,
# link 2048. pin_make.py holds descriptions to 500 (what shows without "more").
LIMITS = {"title": 100, "description": 800, "alt_text": 500, "link": 2048}


# ---------------------------------------------------------------- environment and token


def environment() -> str:
    return "sandbox" if os.environ.get("PINTEREST_SANDBOX", "").strip() in ("1", "true", "yes") else "production"


def read_env_file() -> dict[str, str]:
    env: dict[str, str] = {}
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def setting(key: str) -> str | None:
    return os.environ.get(key) or read_env_file().get(key) or None


def token(env: str) -> str | None:
    if env == "sandbox":
        return setting("PINTEREST_SANDBOX_TOKEN") or setting("PINTEREST_ACCESS_TOKEN")
    return setting("PINTEREST_ACCESS_TOKEN")


def need_token(env: str) -> str:
    t = token(env)
    if not t:
        name = "PINTEREST_SANDBOX_TOKEN or PINTEREST_ACCESS_TOKEN" if env == "sandbox" else "PINTEREST_ACCESS_TOKEN"
        sys.exit(f"no Pinterest token: put {name} in {ROOT / '.env'} (see marketing/pinterest/README.md). "
                 "Nothing was sent.")
    return t


# ---------------------------------------------------------------- HTTP


class PinterestError(RuntimeError):
    pass


def api(method: str, path: str, tok: str, env: str, body: dict | None = None, query: dict | None = None) -> dict:
    """One API call. The token only ever goes in the Authorization header, never into messages."""
    url = f"{API[env]}/{path.lstrip('/')}"
    if query:
        url += "?" + urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {tok}", "Accept": "application/json", "User-Agent": UA}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        text = e.read().decode(errors="replace")
        try:
            msg = json.loads(text).get("message") or text
        except json.JSONDecodeError:
            msg = text
        hint = ""
        if e.code == 401:
            hint = " (token expired or wrong: run --refresh or make a new one, see README)"
        elif e.code == 403:
            hint = " (missing scope, or a trial app calling production: try PINTEREST_SANDBOX=1)"
        elif e.code == 429:
            hint = " (rate limited: try again later)"
        raise PinterestError(f"{method} {path}: HTTP {e.code}: {msg[:300]}{hint}") from None
    except urllib.error.URLError as e:
        raise PinterestError(f"{method} {path}: {e.reason}") from None


# ---------------------------------------------------------------- pins


def load_manifest(path: Path = MANIFEST) -> list[dict]:
    if not path.exists():
        sys.exit(f"no manifest at {path}: render pins first (scripts/marketing/pin_make.py)")
    return json.loads(path.read_text())["pins"]


def load_boards() -> dict[str, dict]:
    return yaml.safe_load(BOARDS_YAML.read_text())


def pin_payload(pin: dict, board_id: str, image_url: str) -> dict:
    """The exact JSON body for POST /v5/pins (PinCreate). Pure: no I/O."""
    body = {
        "board_id": board_id,
        "title": pin["title"],
        "description": pin["description"],
        "link": pin["link"],
        "alt_text": pin["alt_text"],
        "media_source": {"source_type": "image_url", "url": image_url},
    }
    for key, limit in LIMITS.items():
        if len(body[key]) > limit:
            raise ValueError(f"{pin['id']}: {key} is {len(body[key])} characters (Pinterest allows {limit})")
    if not image_url.startswith("https://"):
        raise ValueError(f"{pin['id']}: image url must be https")
    return body


def read_log() -> list[dict]:
    if not LOG.exists():
        return []
    return [json.loads(line) for line in LOG.read_text().splitlines() if line.strip()]


def pinned_ids(env: str) -> set[str]:
    return {e["id"] for e in read_log() if e.get("env") == env}


def write_log(entry: dict) -> None:
    with LOG.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def board_ids_cached(env: str) -> dict[str, str]:
    if not BOARD_IDS.exists():
        return {}
    return json.loads(BOARD_IDS.read_text()).get(env, {})


def save_board_ids(env: str, ids: dict[str, str]) -> None:
    data = json.loads(BOARD_IDS.read_text()) if BOARD_IDS.exists() else {}
    data[env] = dict(sorted(ids.items()))
    BOARD_IDS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def list_boards(tok: str, env: str) -> dict[str, str]:
    """All the account's boards, name → id (follows the bookmark through every page)."""
    out: dict[str, str] = {}
    bookmark = None
    while True:
        page = api("GET", "boards", tok, env, query={"page_size": 250, "bookmark": bookmark})
        for b in page.get("items", []):
            out[b["name"]] = b["id"]
        bookmark = page.get("bookmark")
        if not bookmark:
            return out


def boards_cmd(tok: str, env: str, create: bool) -> None:
    live = list_boards(tok, env)
    wanted = load_boards()
    for key, b in wanted.items():
        if b["name"] in live:
            continue
        if create:
            made = api("POST", "boards", tok, env,
                       body={"name": b["name"], "description": " ".join(b["description"].split()), "privacy": "PUBLIC"})
            live[made["name"]] = made["id"]
            print(f"created board {made['name']!r} ({made['id']})")
        else:
            print(f"missing board {b['name']!r} (key {key}): run with --create")
    for name, bid in sorted(live.items()):
        print(f"  {bid}  {name}")
    save_board_ids(env, live)
    print(f"saved {len(live)} board ids for {env} to {BOARD_IDS.relative_to(ROOT)}")


def check(tok: str, env: str) -> None:
    acct = api("GET", "user_account", tok, env)
    print(f"{env}: @{acct.get('username')} ({acct.get('account_type', '?')}), "
          f"{acct.get('board_count', '?')} boards, {acct.get('pin_count', '?')} pins, "
          f"{acct.get('follower_count', '?')} followers")


def refresh() -> None:
    """POST /v5/oauth/token grant_type=refresh_token with Basic app auth; rewrites the token line in .env."""
    app_id, secret, rtok = setting("PINTEREST_APP_ID"), setting("PINTEREST_APP_SECRET"), setting("PINTEREST_REFRESH_TOKEN")
    if not (app_id and secret and rtok):
        sys.exit("--refresh needs PINTEREST_APP_ID, PINTEREST_APP_SECRET and PINTEREST_REFRESH_TOKEN in .env")
    basic = base64.b64encode(f"{app_id}:{secret}".encode()).decode()
    data = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": rtok}).encode()
    req = urllib.request.Request(f"{API['production']}/oauth/token", data=data, method="POST", headers={
        "Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            got = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"refresh failed: HTTP {e.code} (check the app id/secret and refresh token)")
    path = ROOT / ".env"
    lines = path.read_text().splitlines() if path.exists() else []
    updates = {"PINTEREST_ACCESS_TOKEN": got["access_token"]}
    if got.get("refresh_token"):
        updates["PINTEREST_REFRESH_TOKEN"] = got["refresh_token"]
    for key, value in updates.items():
        for i, line in enumerate(lines):
            if line.split("=", 1)[0].strip() == key:
                lines[i] = f"{key}={value}"
                break
        else:
            lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n")
    days = int(got.get("expires_in", 0)) // 86400
    print(f"new access token saved to .env (expires in about {days} days); not printed")


def show_request(env: str, body: dict) -> None:
    print(f"POST {API[env]}/pins")
    print("Authorization: Bearer <redacted>")
    print("Content-Type: application/json")
    print(json.dumps(body, indent=2, ensure_ascii=False))


def publish(pins: list[dict], env: str, dry_run: bool, limit: int, only: list[str] | None, force: bool) -> int:
    done = pinned_ids(env)
    todo = [p for p in pins if (not only or p["id"] in only)]
    if only:
        unknown = set(only) - {p["id"] for p in pins}
        if unknown:
            sys.exit(f"not in the manifest: {', '.join(sorted(unknown))}")
    if not force:
        todo = [p for p in todo if p["id"] not in done]
    todo = todo[:limit]
    if not todo:
        print(f"nothing to pin ({len(done)} already pinned in {env})")
        return 0

    boards = load_boards()
    if dry_run:
        tok = None
        ids = board_ids_cached(env)
    else:
        tok = need_token(env)
        ids = list_boards(tok, env)
        save_board_ids(env, ids)

    sent = 0
    with tempfile.TemporaryDirectory() as tmp:
        for pin in todo:
            board_name = boards[pin["board"]]["name"]
            board_id = ids.get(board_name)
            if not board_id:
                if not dry_run:
                    sys.exit(f"board {board_name!r} doesn't exist in {env}: run --boards --create first")
                board_id = f"<id of board {board_name!r}>"
            image = ROOT / pin["image"]
            url = P.host(image, Path(tmp), dry_run)
            body = pin_payload(pin, board_id, url)
            print(f"\n# {pin['id']}  ({env}{', dry run' if dry_run else ''})  image {pin['image']}")
            show_request(env, body)
            if dry_run:
                continue
            made = api("POST", "pins", tok, env, body=body)
            write_log({"id": pin["id"], "env": env, "pin_id": made.get("id"), "board": board_name,
                       "image_url": url, "link": pin["link"], "sha256": pin.get("sha256"),
                       "pinned_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
            print(f"pinned {pin['id']}: https://www.pinterest.com/pin/{made.get('id')}/")
            sent += 1
    if dry_run:
        print(f"\ndry run: {len(todo)} pin(s) shown; nothing uploaded or sent")
    return sent


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest", nargs="?", default=str(MANIFEST), help="manifest.json from pin_make.py")
    ap.add_argument("--dry-run", action="store_true", help="print each request; no upload, no API call")
    ap.add_argument("--limit", type=int, default=3, help="at most this many pins this run (default 3)")
    ap.add_argument("--only", nargs="+", metavar="ID", help="only these pin ids")
    ap.add_argument("--force", action="store_true", help="pin again even if pinned.jsonl has it")
    ap.add_argument("--check", action="store_true", help="GET /v5/user_account and stop")
    ap.add_argument("--boards", action="store_true", help="list boards and save their ids")
    ap.add_argument("--create", action="store_true", help="with --boards: create missing boards from boards.yaml")
    ap.add_argument("--refresh", action="store_true", help="refresh the access token into .env")
    args = ap.parse_args(argv)
    env = environment()
    try:
        if args.refresh:
            return refresh()
        if args.check:
            return check(need_token(env), env)
        if args.boards:
            return boards_cmd(need_token(env), env, args.create)
        publish(load_manifest(Path(args.manifest)), env, args.dry_run, args.limit, args.only, args.force)
    except PinterestError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
