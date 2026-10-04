# MAL Profile Kit

Everything needed to rebuild and update Matthew's custom MyAnimeList "About Me": the black / white / gold design with Satsuki Kiryūin, the 推し FAVORITES section, and the live stats card.

The whole About Me is **one image** (MAL's Classic About Me only accepts BBCode, so a designed profile = a hosted image). This kit regenerates that image from a settings file, pulling your **live stats and cover art straight from MAL** every time.

**It updates itself.** GitHub rebuilds the image every day and puts it at one permanent link, which is what your MAL About Me shows:

- Live image: https://raw.githubusercontent.com/Git-Matthew/mal-profile/live/mal_profile.png
- Repo (the live copy of this kit): https://github.com/Git-Matthew/mal-profile
- MAL About Me (Classic) contains: `[center][img]https://raw.githubusercontent.com/Git-Matthew/mal-profile/live/mal_profile.png[/img][/center]`

---

## Two copies of the kit

| Copy | What it's for |
|---|---|
| **GitHub repo** `Git-Matthew/mal-profile` | The **live** one. Its daily job builds from it. Change `config.json` / the design **here** for changes to show up. |
| **This folder** (`Downloads\MAL Profile Kit`) | Backup + extras the repo doesn't need: old versions, your profile picture, cached data. Keep it in sync when something changes. |

## The fastest way to change anything

- **Ask Claude:** open a new Claude chat (Cowork), paste the prompt from **`PROMPT_FOR_NEW_CHAT.md`**, and say what you want (*"swap my #3 anime for Frieren"*, *"I want 5 manga now"*). Claude updates the repo and this folder; the image rebuilds by itself.
- **Do it yourself on GitHub:** open `config.json` in the repo → pencil icon → edit → **Commit changes**. The image rebuilds in ~1 minute; MAL shows it within ~5 more minutes.
- **Fresh stats right now:** repo → **Actions** → *Update MAL profile image* → **Run workflow**.

No more uploading or clicking Submit on MAL: it always shows whatever is at the permanent link.

**Privacy:** the repo is on Matthew's personal GitHub, so the MAL username is kept out of every file there. GitHub reads it from the hidden repo secret `MAL_USERNAME` (Settings → Secrets and variables → Actions); the local kit reads it from `local_settings.json`, which never goes to GitHub (nor does `PROMPT_FOR_NEW_CHAT.md`). The only places it appears are inside the image itself and on MAL.

## What updates by itself vs. what you edit

| Thing | How it updates |
|---|---|
| Mean score, completed count, manga volumes | **Automatic, daily** (09:23 UTC ≈ 3:23 am Mérida) from your MAL list |
| Cover art | **Automatic** from each title's MAL page |
| Which favorites + their order | Edit `config.json` → `favorites` (up to 5 anime, up to 5 manga) |
| Name, motto, quote, labels, colors, character art | Edit `config.json` |
| Layout for 4–5 manga | **Automatic**: stats card becomes a strip under the manga row (see `reference/example_5_manga_layout.png` in the local copy) |

## How the auto-update works

`.github/workflows/update-profile.yml` (in the repo; a copy lives in `github_actions/` here) runs on GitHub's computers, so your PC can be off:

1. Every day, when you press **Run workflow**, or when `config.json` / the design changes in the repo.
2. It runs `build.py` (live stats + covers), then replaces the image on the repo's `live` branch. That branch always holds a single commit, so the repo never grows.
3. GitHub caches the image for up to 5 minutes; MAL just redirects to the link, so it shows the new image right after.

It's free because the repo is public. If a run ever fails (MAL down, etc.), GitHub emails you and the next day's run fixes it. GitHub pauses scheduled jobs in public repos after 60 days with no activity, but the daily update counts as activity; if it's ever paused anyway, Actions tab → *Update MAL profile image* → **Enable workflow**.

## Folder map

```
MAL Profile Kit/
├── README.md                  ← you are here
├── PROMPT_FOR_NEW_CHAT.md     ← paste into a new Claude chat if this one is lost        [local only]
├── local_settings.json        ← your MAL username (the repo uses a secret instead)      [local only]
├── config.json                ← THE file you edit (favorites, text, colors, stats rules)
├── build.py                   ← rebuilds the image (fetch stats + covers → render PNG)
├── requirements.txt           ← Python dependency (Pillow)
├── .gitignore                 ← what the repo leaves out
├── github_actions/
│   └── update-profile.yml     ← copy of the daily GitHub job (in the repo it lives in .github/workflows/)
├── template/
│   └── profile_template.html  ← the design itself (HTML/CSS with placeholders)
├── assets/
│   ├── character/satsuki_sparkle.png   ← your transparent Satsuki art (no effects added)
│   ├── fonts/                 ← Anton, Oswald, Share Tech Mono, Noto Sans JP, DejaVu Sans (bundled)
│   └── posters/               ← auto-downloaded cover art cache
├── tools/
│   └── measure_pairs.py       ← checks every Japanese + English pair has the same visible height
├── data/                      ← auto: cached list data + last computed stats
├── output/                    ← auto: latest image + its HTML
├── versions/                  ← every design so far + VERSION_HISTORY.md (links)       [local only]
├── reference/
│   ├── DESIGN_NOTES.md        ← the design spec + every decision/preference (read before changing looks)
│   ├── MAL_TECH_NOTES.md      ← MAL's rules, hosting, the GitHub setup, and every gotcha
│   └── example_5_manga_layout.png                                                   [local only]
└── profile_picture/           ← your MAL avatar (original + black-bordered version)  [local only]
```

## Running it on your own PC (optional)

Easiest is to let GitHub or Claude run it. To run it yourself:

1. Install Python 3 (python.org), then in this folder: `pip install pillow`
2. Run `python build.py`. It uses Edge/Chrome automatically to render → `output/mal_profile.png`.

Useful commands:
- `python build.py --stats` — just print your current numbers
- `python build.py find "Frieren" --type anime` — get the `mal_id` for a new favorite
- `python build.py --offline` — rebuild without internet (uses cached data/covers)
- `python build.py --config test.json` — try a variant without touching your real config
- `python build.py --no-archive` — preview without saving a dated copy into `versions/`

## Common edits (all in `config.json`)

- **Change / reorder favorites:** edit `favorites.anime` / `favorites.manga` (rank = list order). Each entry needs a `mal_id` (number in the MAL URL) and the `caption` shown under the cover.
- **5 manga instead of 3:** just list 5. The layout switches automatically.
- **Motto / name / quote / labels:** `hero`, `footer_quote`, `favorites_section`. (If you change Japanese or English text a lot, ask Claude to re-check that each pair still has the same visible height.)
- **Black or white pieces:** `theme`. `header_bar`, `favorites_bar`, `stats_box` and `footer_bar` can each be `"dark"` (black, white text) or `"light"` (white, black text); `stats_labels` and `captions` can be `"gray"` or `"black"`. Current: bars black, stats box white with black text, cover titles black.
- **Stats rows:** `stats.rows` (pick from the value keys listed in the file). Counting rules live in `stats.rules` (currently: anime = completed only; manga volumes = completed + reading).
- **New character art:** drop a transparent PNG in `assets/character/`, point `character.image` at it, then tweak `height_px` / `top_px` / `right_px`. The name tag auto-moves to the art's left edge (set `name_tag.enabled` false if the new art doesn't need it).

Limits to respect: the image must stay **≤ 1000px tall** (MAL folds the rest behind "Read More") and **798px wide** (MAL's max). The build warns you if you go over.

## Your profile picture

`profile_picture/mal_pfp_bordered.png` (already on your MAL). Same ink-black border as the design.
