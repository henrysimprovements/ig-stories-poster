"""Post due Instagram Stories from schedule.json using the Instagram Graph API.

Runs from GitHub Actions every 15 minutes. A story is "due" when its post_at time
has passed and its id is not yet in posted.json. Images must be public URLs
(the raw GitHub URL of a file in images/ works when the repo is public).
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

GRAPH = "https://graph.facebook.com/" + os.environ.get("GRAPH_VERSION", "v21.0")
TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
IG_USER_ID = os.environ.get("IG_USER_ID", "")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
DRY_RUN = os.environ.get("DRY_RUN") == "1"
# Skip anything more than this late, so a broken run never dumps a backlog at once.
MAX_LATE = timedelta(hours=int(os.environ.get("MAX_LATE_HOURS", "6")))


def api(method, path, params):
    params = dict(params, access_token=TOKEN)
    data = urllib.parse.urlencode(params).encode()
    url = f"{GRAPH}/{path}"
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode())
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> {e.code}: {e.read().decode()}") from None


def image_url(story):
    img = story["image"]
    if img.startswith("http"):
        return img
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{img}"


def publish(story):
    url = image_url(story)
    if DRY_RUN:
        print(f"  [dry run] would post {url}")
        return "dry-run"
    container = api("POST", f"{IG_USER_ID}/media", {"image_url": url, "media_type": "STORIES"})["id"]
    for _ in range(30):  # wait up to ~5 min for Instagram to process the image
        status = api("GET", container, {"fields": "status_code"}).get("status_code")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {container} status {status}")
        time.sleep(10)
    else:
        raise RuntimeError(f"container {container} never finished processing")
    return api("POST", f"{IG_USER_ID}/media_publish", {"creation_id": container})["id"]


def main():
    if not DRY_RUN and not (TOKEN and IG_USER_ID):
        sys.exit("Missing IG_ACCESS_TOKEN or IG_USER_ID secret")
    schedule = json.load(open("schedule.json"))
    posted = json.load(open("posted.json")) if os.path.exists("posted.json") else {}
    now = datetime.now(timezone.utc)
    failures = 0
    for story in schedule:
        sid = story["id"]
        if sid in posted:
            continue
        when = datetime.fromisoformat(story["post_at"])
        if when > now:
            continue
        if now - when > MAX_LATE:
            print(f"SKIP {sid}: more than {MAX_LATE} late")
            posted[sid] = {"skipped": "too late", "at": now.isoformat()}
            continue
        print(f"POST {sid} ({story['post_at']})")
        try:
            media_id = publish(story)
            posted[sid] = {"media_id": media_id, "at": now.isoformat()}
            print(f"  ok, media id {media_id}")
        except Exception as e:  # keep going; it retries on the next run
            failures += 1
            print(f"  FAILED: {e}")
    if not DRY_RUN:
        json.dump(posted, open("posted.json", "w"), indent=2)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
