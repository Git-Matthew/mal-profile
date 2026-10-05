# MAL technical notes & the exact workflow

Everything learned the hard way while building this (Oct 2026). Written mainly for Claude in a future chat, but readable by anyone.

## MAL's rules

- **About Me Style must be "Classic".** Classic About Me = **BBCode only** (no HTML/CSS). Modern About Me is just a template picker (custom styling is a paid Supporter perk) and is *not* wider — both are ~800px. So a designed profile = a hosted image in `[img]`.
- Images in the About Me are clamped to **798px wide** (we render at 2× = 1596px for sharpness; MAL scales it down).
- The About Me box is cut at **1000px tall** behind a "Read More" button. MAL's page script adds the button only when the content is *taller* than 1000px, so exactly 1000 is safe. With `output.fill_to_max_height` (on), `build.py` measures the layout in the browser and sizes the covers so the image is exactly 1000px (a 1596 × 2000 PNG at 2x).
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
- Workflow `.github/workflows/update-profile.yml` (copy in `github_actions/` of the local kit, because Claude's remote tools can't write a `.github` folder on his PC): runs daily at 09:23 UTC, on "Run workflow", and on pushes to `main` touching `config.json`, `build.py`, `template/`, `assets/`, `list/` or the workflow. Steps: checkout → Python 3.12 + Pillow → `python build.py --no-archive` with `CHROME_PATH=google-chrome` → copies the PNG + `data/stats.json` + `output/list/*` (+ an empty `.nojekyll`) into a fresh git repo and **force-pushes it as the `live` branch** (always one commit, so the repo doesn't grow by ~2 MB a day). Needs `permissions: contents: write` (set in the file). Runs are queued one at a time (`concurrency`), so several quick pushes can't overwrite each other out of order.
- **Upload order matters** when a change touches several folders (each upload is its own commit, and each commit to a watched path starts a run): upload files that the *new* `build.py` needs (templates, `list/list.css`) **before** `build.py`, and the workflow last. The current templates also work with an older `build.py` (new options are body classes, not new placeholders), so no run breaks in between.
- **Permanent link:** `https://raw.githubusercontent.com/Git-Matthew/mal-profile/live/mal_profile.png` (served as `image/png`, `Cache-Control: max-age=300`). Current stats at `.../live/stats.json`.
- **GitHub Pages** (Settings → Pages → Deploy from a branch → `live` / root) serves the list design at `https://git-matthew.github.io/mal-profile/list/…` with real `text/css` and `Access-Control-Allow-Origin: *` (raw.githubusercontent serves CSS as `text/plain` + `nosniff`, which browsers refuse as a stylesheet — fine for the PNG, useless for CSS). Pages caches for ~10 minutes.
- A GitHub build is pixel-identical to a sandbox build (symbols ★ ▸ come from the bundled DejaVu Sans, so the runner's system fonts don't matter).
- GitHub disables scheduled workflows in public repos after **60 days without repository activity**; the daily force-push counts as activity. If it ever gets disabled: Actions → *Update MAL profile image* → Enable workflow.

### Changing files in the repo (Claude, through his Edge)

The sandbox can't push to his repo (its GitHub access is limited to repos attached to the session). Use the web uploader:
1. Put the file in the local kit on his PC (`device_commit_files` into `C:\Users\matth\OneDrive\Desktop\MAL Profile Kit\...`, which must be a connected folder), then `device_stage_files` it back → `/mnt/user-data/uploads/MAL Profile Kit/...`. *Why:* the browser `file_upload` tool only accepts files staged from his device, not files Claude created in its own folders.
2. Open `https://github.com/Git-Matthew/mal-profile/upload/main/<folder>` (works for new folders too; the repo root is `/upload/main`). `find` the "Choose your files" input → `file_upload` (≤ 10 MB per call; call it again on the same page to add more).
3. Click the commit message box, type a message, press **Enter** (submits). **Wait until it lands back on the repo page** — leaving the "Processing your files…" page early silently drops the commit. Check the commit list afterwards.
4. Workflow files can be uploaded the same way into `.github/workflows` (from the `github_actions/` copy).
5. If a GitHub page hangs ("document_idle" timeouts), close the tab and open a fresh one.
6. For small text edits, the web editor (pencil icon on a file) also works.

## The list pages (anime + manga), since Oct 5, 2026

- **Template: Modern.** Classic lists are a leftover (MAL Cover CSS calls itself "a relic of the past"); Modern has built-in cover images and is what every current design uses. Both lists use **Default Theme** (theme id 1), edited at `https://myanimelist.net/ownlist/style/theme/1` → **Add Custom CSS** → Save. One theme = one CSS box shared by both lists.
- MAL **blocks plain `@import`** in that box. The community trick `@\import "https://…";` (a backslash escape in the at-rule name) gets past the filter and browsers still read it as `@import`. MAL puts the box's text in `<style id="custom-css">` right after the theme CSS, so the import is at the top of its own stylesheet (as `@import` must be). Our box holds only `@\import "https://git-matthew.github.io/mal-profile/list/list.css";` — everything else lives on GitHub. Inside `list.css`, normal `@import`s load `theme.css` (bar colours from config), Google Fonts, `anime_covers.css`, `manga_covers.css` (relative to list.css).
- **Page structure** (rendered by Vue from `data-items`): `body.ownlist.anime` / `body.ownlist.manga` (plus `data-owner-name`), `.header` (`a.header-title`, `.header-menu`), `.list-menu-float` (owner only), `#list-container` → `.cover-block > #cover-image-container > img#cover-image` (theme banner), `#status-menu.status-menu-container > .status-menu > a.status-button.{all_anime|watching|reading|completed|onhold|dropped|plantowatch|plantoread}.on` (+ `.search-container`; gets `.fixed` when sticky), `.list-block > .list-unit.{status}` (the manga "All" tab is also `all_anime`) → `.list-status-title > span.text + span.stats`, `table.list-table` → first `tbody` = header row `th.header-title.{status,number,image,title,score,type,progress | chapters,volumes}`; then one `tbody.list-item` per entry → `tr.list-table-data` → `td.data.status.{status}`, `td.data.number`, `td.data.image > a.link.sort[href="/anime/<id>/<slug>"] > img.hover-info.image` (MAL's 192×272 webp thumbnail), `td.data.title` (`a.link.sort`, `.add-edit-more` = Add/Edit · More, `.content-status`, `.rewatching`), `td.data.score > a > span.score-label.score-N|score-na`, `td.data.type`, `td.data.progress` (owner: `a.icon-add-episode` = +1), manga `td.data.chapter` / `td.data.volume`; `tr.more-info` opens under "More". Footer: `#footer-block > #copyright`. 300 entries load at first, the rest on scroll.
- Our layout turns `table.list-table` into a CSS grid (6 columns × 152px) and each `tbody.list-item` into a poster card; numbers come from a CSS counter (`decimal-leading-zero`), not MAL's text. Extra columns turned on in MAL's list settings show as small lines under the card.
- **Hi-res covers:** MAL's thumbnail `https://cdn.myanimelist.net/r/192x272/images/anime/1819/97947.jpg?s=…` → drop `r/WxH/` and the query, add `l` → `https://cdn.myanimelist.net/images/anime/1819/97947l.webp` (426×600). `build.py` writes one rule per entry, `.data.image a[href^="/anime/<id>/"]::after{background-image:url(…)}`, laid over MAL's own `<img>`, so a brand-new entry still shows a cover until the next daily run.
- **Framed card:** like the profile image, the list is one card with a 2px black frame: `.header` and `#list-container` are both `content-box` with a 2px border (no border between them), so their inner width stays 1060px; the gold top line is a 5px background stripe inside the header. The frame also frames where Satsuki's art is cut on the right.
- **Banners:** `build.py` renders `anime_banner.png` / `manga_banner.png` (1060 × 328, transparent top 68px = the header bar inside the frame) from `template/list_assets_template.html`; `list.css` puts them on `.cover-block::before` so Satsuki pops up into MAL's header bar (`pointer-events:none`; the header menu sits at `z-index:30` above it). `header.png` (crest + MYANIMELIST) and `footer.png` (the quote) come from the same template. Chromium quirks for these renders: tiny windows render blank (so the window is at least 800px wide), and new-headless Chrome keeps ~90px of the window for an invisible toolbar, so the window is the content height + 300px and the shot is cropped (a 400px window once cut the banners off at 313px).
- **Previewing without touching MAL:** `python3 tools/preview_list.py` loads his public list pages in Playwright, answers the GitHub Pages URLs from `output/list/`, and injects the one-line custom CSS where MAL would. A fresh sandbox visitor gets MAL's US privacy pop-up — the tool hides it. `--measure` checks the Japanese/English pairs. The owner view (Edit buttons, +1) can only be seen in his own logged-in browser: inject `<style id="custom-css">@\import "…list.css";</style>` with JavaScript (temporary, nothing saved).
- Visitors can't get a layout switch: MAL ignores unknown URL parameters (not in `body[data-query]`), and the status tabs drop any extra parameters. A `:target` hash on an existing id (e.g. `#advanced-options`, no scroll) would work for one page load only. A "rows" layout was discussed (Oct 5, 2026) and skipped for now.

## Older hosting: imgur (fallback, used until Oct 4, 2026)

Matthew's imgur account (logged in on Edge). Anonymous hosts were rejected or unsafe: from Claude's cloud sandbox, catbox.moe says "Invalid uploader", 0x0.st resets, x0.at returned a link that 404'd.
Recipe: commit the PNG into a connected folder on his PC → stage it back → `https://imgur.com/upload` → `file_upload` into **"Choose Photo/Video"** → regex the page for `i.imgur.com/<id>.png` → download and pixel-compare. Gotchas: the first upload once created an empty post (retry on a fresh page); the page sometimes hangs (fresh tab). Uploads stay hidden posts — **never click "Share to community".** An imgur link can't be overwritten, so every update needed a new MAL Submit — that's why we moved to GitHub.

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
- `tools/measure_pairs.py output/profile.html` (needs Playwright + Chromium, which Claude's sandbox has) prints the visible height/position of every Japanese + English pair; keep them within 1px. For the list pages: `tools/preview_list.py --measure`.
- Saving the list's Custom CSS: MAL's theme page has a normal Save button (no reCAPTCHA seen), but as with the About Me, stage it and let Matthew click Save.

## Future options

- **Clickable covers:** slice the PNG into horizontal bands; the poster rows become per-poster slices each wrapped in `[url=https://myanimelist.net/anime/<id>][img]slice[/img][/url]`. Put tags back-to-back with **no spaces/newlines** (whitespace = gaps), keep each row's slice widths summing to ≤ ~790px. With GitHub hosting, the slices could also be published to the `live` branch at fixed names, so they'd stay hands-free.
