"""Approve held Instagram Stories in schedule.json.

Run from GitHub Actions with the "Approve stories" button. Stories that Claude
adds with "approved": false are held by post_stories.py until this runs.
WEEK (optional, YYYY-MM-DD of the Monday) limits approval to that week;
blank approves every held story.
"""
import json
import os
from datetime import date, datetime, timedelta

week = os.environ.get("WEEK", "").strip()
start = end = None
if week:
    start = date.fromisoformat(week)
    end = start + timedelta(days=7)

schedule = json.load(open("schedule.json"))
approved = []
for story in schedule:
    if story.get("approved") is not False:
        continue
    day = datetime.fromisoformat(story["post_at"]).date()
    if start and not (start <= day < end):
        continue
    story["approved"] = True
    approved.append(story["id"])

json.dump(schedule, open("schedule.json", "w"), indent=2)
open("schedule.json", "a").write("\n")
print(f"Approved {len(approved)} stories:" if approved else "No held stories to approve.")
for sid in approved:
    print(f"  {sid}")
