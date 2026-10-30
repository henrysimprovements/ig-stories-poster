# Henry's Improvements: Instagram Stories poster

Posts Instagram Stories on a schedule straight through Meta's Instagram API,
so Metricool's free 20 posts a month can all go to TikTok.

## How it works
1. Story images go in `images/` (1080x1920 PNG or JPG).
2. Each story gets a line in `schedule.json`: an id, the time to post (with the
   `-05:00` Eastern offset), and the image path.
3. Every 15 minutes GitHub runs `post_stories.py`. It posts anything that is due
   and writes it to `posted.json`, so nothing posts twice.
4. Nothing posts unless it is in `schedule.json`, and Claude only adds stories
   after Javier approves them.

The repo must be **public** so Instagram can fetch the images from GitHub. The
access token stays private in GitHub Secrets and is never in the code.

## One-time setup (about 20 minutes)
Instagram must be a **Business** (or Creator) account linked to the Henry's
Improvements Facebook Page. It already is if Metricool and Zoho can post to it.

1. **Create a Meta app.** Go to developers.facebook.com, choose My Apps, then
   Create App, then type "Business". Name it "Henry Stories".
2. **Add a System User.** In business.facebook.com, open Settings, then Users,
   then System Users. Add one named "stories-bot" with the Admin role. Click
   Add Assets and give it the Facebook Page and the Instagram account (full
   control), and the "Henry Stories" app.
3. **Make the token.** On that System User, click Generate New Token, pick the
   "Henry Stories" app, set expiry to **Never**, and tick these permissions:
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement`, `business_management`. Copy the token.
4. **Find the Instagram user ID.** Open this in a browser with your token pasted in:
   `https://graph.facebook.com/v21.0/me/accounts?fields=name,instagram_business_account&access_token=YOUR_TOKEN`
   The number under `instagram_business_account` → `id` is the IG user ID.
5. **Add GitHub secrets.** In this repo, open Settings, then Secrets and
   variables, then Actions, then New repository secret. Add:
   - `IG_ACCESS_TOKEN`: the token from step 3
   - `IG_USER_ID`: the number from step 4
6. **Turn on Actions.** Open the Actions tab and enable workflows if asked.

## Test it
Put one image in `images/`, add a schedule line a few minutes in the past, then
go to Actions → Post Instagram Stories → Run workflow. Check that the story is
on Instagram and in `posted.json`.

## Notes
- Instagram's API allows 50 published posts per 24 hours. 2 stories a day is
  nowhere near that.
- Anything more than 6 hours late is skipped rather than posted late.
- Stories posted this way can't have stickers or links. They post the image only.
