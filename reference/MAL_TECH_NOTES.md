# MAL technical notes & the exact workflow

Everything learned the hard way while building this (Oct 2026). Written mainly for Claude in a future chat, but readable by anyone.

## MAL's rules

- **About Me Style must be "Classic".** Classic About Me = **BBCode only** (no HTML/CSS). Modern About Me is just a template picker (custom styling is a paid Supporter perk) and is *not* wider — both are ~800px. So a designed profile = a hosted image in `[img]`.
- Images in the About Me are clamped to **798px wide** (we render at 2× = 1596px for sharpness; MAL scales it down).
- The About Me box is cut at **1000px tall** behind a "Read More" button → keep the image ≤ 1000px (current: ~950px; 5-manga layout ~984px).
- MAL rewrites outside image links to its own proxy (`image.myanimelist.net/ui/<token>`). The proxy just **302-redirects to the original link**, so the original must stay online, and replacing the file at the same link changes what MAL shows. To check which image is live: take the proxy link from the About Me on the public profile page and request it without following redirects — the `Location` header is the real URL.
- Useful BBCode: `[center]`, `[img]url[/img]`, `[url=link]text or [img][/img][/url]` (clickable), `[size=N]` (percent), `[color=#hex]`, `[spoiler=Label]…[/spoiler]` (dropdown button), `[yt]VIDEO_ID[/yt]` (playable YouTube), animated GIFs work.
- Profile avatar shows at ~225px wide.

## Where the data comes from (build.py does this)

- Full lists (public): `https://myanimelist.net/animelist/<username>/load.json?status=7&offset=0` and `/mangalist/...` — 300 items per page, page with `offset`.
  Status codes: **1** watching/reading · **2** completed · **3** on hold · **4** dropped · **6** plan to watch/read.
  Fields used: `status`, `score`, `num_watched_episodes`, `num_read_volumes`, `num_read_chapters`.
- Poster art: the `og:image` meta tag on `https://myanimelist.net/{anime|manga}/{mal_id}`.
- Works from Claude's sandbox **and** from GitHub Actions runners (checked Oct 4, 2026).
- The Jikan API (api.jikan.moe) returned 504s from the sandbox — scraping MAL directly is the reliable path.
- MAL's own profile stats page can lag/cache (it showed mean 8.03 while the list computed 7.99) — trust the list data.

## Hosting: GitHub, hands-free (current setup since Oct 4, 2026)

- Public repo **`Git-Matthew/mal-profile`** (Matthew is logged in as Git-Matthew in Edge). Public is required: MAL must load the image without a login, and Actions minutes are free for public repos.
- Repo = this kit **minus** `data/`, `output/`, `assets/posters/`, `versions/`, `profile_picture/`, `local_settings.json`, `PROMPT_FOR_NEW_CHAT.md` (see `.gitignore`).
- **Never put the MAL username in any repo file, commit message or repo description.** The repo is on his personal GitHub and he doesn't want it tied to his MAL name (the image itself showing it is fine). `build.py` reads it from the `MAL_USERNAME` env var (the workflow passes the repo secret of that name; GitHub masks it as `***` in public logs) or from `local_settings.json` (local only). `hero.display_name` is left empty so the image shows the username in capitals without it being written in config.json. The repo was deleted and recreated on Oct 4, 2026 to wipe the username from its history. Accepted trade-off: right-clicking the image on MAL reveals the raw.githubusercontent.com/Git-Matthew link.
- Workflow `.github/workflows/update-profile.yml` (copy in `github_actions/` of the local kit, because Claude's remote tools can't write a `.github` folder on his PC): runs daily at 09:23 UTC, on "Run workflow", and on pushes to `main` touching `config.json`, `build.py`, `template/`, `assets/` or the workflow. Steps: checkout → Python 3.12 + Pillow → `python build.py --no-archive` with `CHROME_PATH=google-chrome` → copies the PNG + `data/stats.json` into a fresh git repo and **force-pushes it as the `live` branch** (always one commit, so the repo doesn't grow by ~2 MB a day). Needs `permissions: contents: write` (set in the file).
- **Permanent link:** `https://raw.githubusercontent.com/Git-Matthew/mal-profile/live/mal_profile.png` (served as `image/png`, `Cache-Control: max-age=300`). Current stats at `.../live/stats.json`.
- A GitHub build is pixel-identical to a sandbox build (symbols ★ ▸ come from the bundled DejaVu Sans, so the runner's system fonts don't matter).
- GitHub disables scheduled workflows in public repos after **60 days without repository activity**; the daily force-push counts as activity. If it ever gets disabled: Actions → *Update MAL profile image* → Enable workflow.

### Changing files in the repo (Claude, through his Edge)

The sandbox can't push to his repo (its GitHub access is limited to repos attached to the session). Use the web uploader:
1. Put the file in the local kit on his PC (`device_commit_files` into `C:\Users\matth\Downloads\MAL Profile Kit\...`), then `device_stage_files` it back → `/mnt/user-data/uploads/Downloads/MAL Profile Kit/...`. *Why:* the browser `file_upload` tool only accepts files staged from his device, not files Claude created in its own folders.
2. Open `https://github.com/Git-Matthew/mal-profile/upload/main/<folder>` (works for new folders too; the repo root is `/upload/main`). `find` the "Choose your files" input → `file_upload` (≤ 10 MB per call; call it again on the same page to add more).
3. Click the commit message box, type a message, press **Enter** (submits). **Wait until it lands back on the repo page** — leaving the "Processing your files…" page early silently drops the commit. Check the commit list afterwards.
4. Workflow files can be uploaded the same way into `.github/workflows` (from the `github_actions/` copy).
5. If a GitHub page hangs ("document_idle" timeouts), close the tab and open a fresh one.
6. For small text edits, the web editor (pencil icon on a file) also works.

## Older hosting: imgur (fallback, used until Oct 4, 2026)

Matthew's imgur account (logged in on Edge). Anonymous hosts were rejected or unsafe: from Claude's cloud sandbox, catbox.moe says "Invalid uploader", 0x0.st resets, x0.at returned a link that 404'd.
Recipe: commit the PNG to his Downloads → stage it back → `https://imgur.com/upload` → `file_upload` into **"Choose Photo/Video"** → regex the page for `i.imgur.com/<id>.png` → download and pixel-compare. Gotchas: the first upload once created an empty post (retry on a fresh page); the page sometimes hangs (fresh tab). Uploads stay hidden posts — **never click "Share to community".** An imgur link can't be overwritten, so every update needed a new MAL Submit — that's why we moved to GitHub.

## Posting to MAL (only needed when the link itself changes)

1. Open `https://myanimelist.net/editprofile.php` in his browser.
2. Make sure the **About Me Style** radio is **Classic**.
3. Set textarea `#classic-about-me-textarea` to `[center][img]LINK[/img][/center]` (dispatch input/change events).
4. **Matthew clicks Submit.** The form has an invisible reCAPTCHA: automated clicks are silently rejected (the old value stays). Don't try to bypass it — scroll the Submit button into view, outline it (e.g. 4px gold), and tell him it's ready. Remind him not to refresh first.
5. Verify afterwards by reloading `editprofile.php` and checking the textarea (or use the proxy-redirect check under "MAL's rules" on the public profile).

## Tool quirks

- Browser JavaScript-tool results that contain URL query strings (`?`, `=`, `&`) can get blocked by a content filter — sanitize outputs (e.g. `.replace(/[?=&]/g,' ')`) or return booleans.
- Script-heavy profile pages (other people's custom profiles) can make the browser screenshot tool time out — don't fight it.
- Headless render command used by build.py: Chromium/Edge `--headless=new --force-device-scale-factor=2 --window-size=798,1200 --screenshot=...`, then crop white margins.
- `tools/measure_pairs.py output/profile.html` (needs Playwright + Chromium, which Claude's sandbox has) prints the visible height/position of every Japanese + English pair; keep them within 1px.

## Future options

- **Clickable covers:** slice the PNG into horizontal bands; the poster rows become per-poster slices each wrapped in `[url=https://myanimelist.net/anime/<id>][img]slice[/img][/url]`. Put tags back-to-back with **no spaces/newlines** (whitespace = gaps), keep each row's slice widths summing to ≤ ~790px. With GitHub hosting, the slices could also be published to the `live` branch at fixed names, so they'd stay hands-free.
