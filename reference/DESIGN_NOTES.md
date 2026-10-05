# Design notes — MAL About Me + list pages

Read this before changing anything visual. It records what the design is, why each piece exists, and every preference Matthew stated while it was built (Oct 2026). **Don't redesign unless asked** — he iterated hard to get here.

## What it is

A single 798 × 1000px image on MAL's Classic About Me (exactly MAL's limit before "Read More"; `build.py` sizes the covers to fill it), built as HTML/CSS (`template/profile_template.html`) and rendered to PNG by `build.py`. It started as a "Honnōji Academy dossier" (Kill la Kill student-council file) and was deliberately toned down into a clean MyAnimeList-branded profile that keeps a little Kill la Kill flavor.

Top to bottom:

1. **Gold top line** (5px) → **header bar** (flat white since Oct 5, 2026; was ink): white diamond crest (gold border) with a MAL-blue **神** (25.5px, centred, ~2.7px clear of the border), black **MYANIMELIST**, gray sub-line **#0001 // ★★★★★** (gold stars), gold dashed rule underneath.
2. **Hero** (white, faint grid on the left that fades out): **the MAL username in capitals** (Anton, **gold** since Oct 5, 2026) over a **gold** underbar with a MAL-blue tip; motto **神のお気に入り** in gold + **GOD'S FAVOURITE** in gray, both the same visible height; chips **● STATUS: ACTIVE** (green dot) and **MEAN SCORE ★ x.xx**.
3. **Satsuki** (his transparent sparkle PNG) on the right. The *whole* image — hair and sparkles — rides **over the header** for a 3D "pop-out" feel, and is clipped only where the Favorites bar starts. **No effects on her** (no shadow, no glow, no outline).
4. **Name tag**: slim white tag, **black outline**, gold top cap, gold **★** and gold vertical **鬼龍院皐月**, rising from the Favorites bar to mid-height. It exists to hide where the art's hair runs into the image edge (the source art is cropped there). `build.py` auto-positions it on that edge.
5. **Favorites bar** (flat white with black lines above and below; was ink): gold **推し** block (white text, like the rank badges) + black **FAVORITES** (same visible height).
6. **▸ TOP ANIME 鑑賞記録** (label in bold Anton, kanji the same height) — 5 poster cards (black frame, soft offset shadow; **every cover in the image is the same size**: 140px wide, height picked by `build.py` so the image is exactly 1000px, ~219px today), gold rank badge with **white** number, caption under each in **black** (wraps to 2 lines, never truncated).
7. **▸ TOP MANGA 読書記録** — 1–3 manga: cards + **STATS** card (**flat white, black border**, STATS title as big as the numbers (28px title / 26px numbers) + gold ★★★★★, black labels at 15px, gold dashed dividers, faint gold ring in the corner). 4–5 manga: full row + horizontal stats strip in the same style.
8. **Footer** (flat white, gold dashed top; was ink): black **「恐怖こそ自由！」** + gold **FEAR IS FREEDOM** (Japanese 14px; English 16px so its capitals look as tall as the Japanese, i.e. about the kana height. Capitals as tall as the kanji looked bigger to him).

## Palette & type

| Token | Hex | Use |
|---|---|---|
| ink | `#15151c` | frames, text, the lines on the white bars |
| gold | `#d7a736` | top line, dashes, crest border, **name + the bar under it**, motto, rank badges, 推し block, stars |
| blue | `#2e51a2` | MyAnimeList's own blue (its nav bar): 神 kanji, underbar tip, ▸ row arrows |
| green | `#22c55e` | "online" status dot |
| white | `#ffffff` | backgrounds (pure white — no tints) |

Fonts (bundled in `assets/fonts/`): **Anton** (display + titles), **Share Tech Mono** (labels/data), **Oswald** (secondary), **Noto Sans JP Black** (all Japanese), **DejaVu Sans** (only the ★ ▸ symbols, so renders match on every machine).

## Matthew's stated preferences (honor these)

- **White backgrounds.** He removed a faint blue gradient behind the name and wanted the hero pure white. No tinted washes.
- **No "dissolving"/fade effects** on images (he disliked mask fades early on).
- **No effects on the character art.** He asked to remove the drop shadow and white rim: "the plain image is already a png with transparent background, let her be."
- **Full overlay.** The head-only pop-out looked wrong to him; he wanted the *entire* image (with sparkles) over the header.
- **Less Honnōji flavor.** Removed: "Honnōji Academy", student council, "personnel file", "subject designation", three-star/elite tags, sanctioned stamp, "classified/curated by order of the president", "unauthorised viewing" footer, clearance rows. Red was retired entirely (now gold/blue).
- **Kept:** the 神 crest, 推し, the kanji row labels, the name tag, and the quote — **with** the 「！」.
- **Stats rules:** anime counts = **completed only**; manga = **volumes** (he tracks volumes, not chapters) from **completed + reading**; mean = completed scored anime; **Mean Score first**, then Anime Completed, then Manga Volumes; **no episodes row**.
- Number badges: gold background, **white** numbers.
- **Stats box (Oct 3, 2026):** **flat white** (no texture lines: it sits above the page's faint scanline overlay), **black border**, **bigger text** so it doesn't get lost next to the covers. Chosen over the original dark box with a gold border.
- **Black text over light gray** for the stats labels and the cover titles ("I definitely prefer black letters over light gray letters"). Still gray: GOD'S FAVOURITE and the small kanji next to TOP ANIME / TOP MANGA.
- **Bars are white** (header, Favorites, footer) since Oct 5, 2026: he'd seen white versions on Oct 3 and kept black then; with the gold name he tried them again and switched. White bars must be **flat white** (no scanline texture), like the stats box. Black versions are still one `theme` switch away in config.json.
- **Every Japanese + English pair has the same visible height** ("every time there is japanese and english ensure both are same height"): the motto, 推し FAVORITES, TOP ANIME / TOP MANGA + kanji, and the footer quote. Sizes and 1–2px nudges were tuned by measuring the rendered image; re-check with `tools/measure_pairs.py` after any text/size change (keep within 1px). **What counts is how it looks**: in the footer, English capitals as tall as the kanji looked bigger to him, so there the English is ~2.5px shorter than the kanji on purpose (about the kana height).
- **Oct 4, 2026 changes:** (1) all covers the same size; he noticed the manga ones were shorter (they were 122×188 next to 140×198 anime). (2) Image maxed out at exactly 1000px: "i dont want the read more to appear but i do want to max out". `output.fill_to_max_height` makes `build.py` pick the cover height, so text/stat changes just make the covers a bit shorter or taller. (3) Every blue → **MAL blue** `#2e51a2`, except the 推し block → **gold**. (4) 神 crest: MAL-blue kanji on a **white** diamond (picked over blue on the dark diamond, which looked dim). (5) Footer: only the English got smaller; the Japanese size was fine. (6) 神 25% bigger (22.5px, picked over +15/+20%) and centred in the diamond, ~4px clear of the gold border.
- **Oct 5, 2026 changes:** (1) name in **gold** ("i want to see if i like it that way" → kept it) and the bar under it gold too (MAL-blue tip stays). (2) all three bars **white**. (3) 神 bigger again, "without touching the gold borders": 25.5px is the largest that keeps a clear white gap (~2.7px). (4) the anime + manga list pages got the same design (below).
- **Section titles are bold:** TOP ANIME / TOP MANGA use bold Anton ("they are titles technically").
- **STATS matches the numbers' size** so it doesn't lose impact; stats labels big enough to notice what the numbers mean, but not competing with them.
- Captions must wrap rather than cut off ("why didn't it just wrap to 2 lines?").
- He likes seeing options **side by side** before choosing (full pages, not just crops), and wants any MAL Submit staged for him.

## What the Japanese says

| Text | Reading | Meaning |
|---|---|---|
| 神 (crest) | kami | god — echoes his motto |
| 神のお気に入り | kami no okiniiri | "God's favorite" — his motto |
| 鬼龍院皐月 (name tag) | Kiryūin Satsuki | her full name, family name first |
| 推し | oshi | "my faves" / the ones you stan |
| 鑑賞記録 | kanshō kiroku | viewing log |
| 読書記録 | dokusho kiroku | reading log |
| 「恐怖こそ自由！」 | kyōfu koso jiyū | "Fear is freedom!" — opening of Satsuki's speech (Fear is freedom! Subjugation is liberation! Contradiction is truth!) |

## Ideas discussed but not built (yet)

- **Clickable covers**: slice the image so each poster links to its MAL page (see MAL_TECH_NOTES.md). Pair with a "▸ CLICK ANY COVER TO OPEN IT" hint on the Favorites bar.
- "Member since Nov 2024" (joined Nov 10, 2024) somewhere in the header.
- A dropdown/video layer under the image (`[spoiler]` buttons, a playable `[yt]` OP) — he liked this idea in references.
- mal-badges.com was checked: unofficial, works over https, but his badge was blank/ungenerated and its "level" endpoint is dead — replaced by the custom STATS card.

## Profile picture

Ryo Asuka (Devilman Crybaby), `profile_picture/`. Bordered version = 10px `#15151c` border on the 800px image, which shows as ~3px at MAL's 225px avatar size — matching the poster frames. The bordered version is live (checked Oct 3, 2026).

## List pages (anime + manga), since Oct 5, 2026

Same design on MAL's **Modern** list (Default Theme + one `@\import` line; see MAL_TECH_NOTES.md). He asked for it to "follow the same design we have for my profile so its consistent", remembering all his profile preferences, and left Modern vs Classic to Claude.

**The frame** (Oct 5, 2026): like the profile image, two 2px black lines run down the page around the list, from the top of the page to the footer's bottom line. He asked for it ("the entire thing has a black outline around it, which makes the satsuki image look perfect since it'd normally get cut on the right"). The first try boxed everything inside the frame and he didn't like that "it all cuts there": the header and footer bars must run across the **whole page**, through the frame, so the frame reads as "an aesthetic decision in the middle of the page", not a limit, and no space looks wasted. Lines *inside* the list (tabs, title band, STATS drawer) run frame to frame and **meet** the frame lines (he asked for the title band's lines to "touch the borders").

Top to bottom:
1. **Header bar** = the profile's, across the whole page: gold top line, white bar, 神 crest + MYANIMELIST (`header.png`), gold dashed rule (dashes lined up with the list's left edge); the frame lines cross it. MAL's "Viewing <user>'s Anime List ▾" menu moved next to the title (Satsuki covers the right side).
2. **Banner** (`anime_banner.png` / `manga_banner.png`, rebuilt daily): the username in gold + gold bar, title pair **鑑賞記録 ANIME LIST** / **読書記録 MANGA LIST** (gold Japanese + gray English, same sizes as the motto, measured equal), chips (● STATUS: ACTIVE · ANIME ▸ COMPLETED n · MEAN SCORE ★ x.xx | MANGA ▸ VOLUMES n · MEAN SCORE ★ x.xx), Satsuki popping out over the header bar (her art's right edge is cut exactly on the right frame line), the 鬼龍院皐月 name tag.
3. **Tabs**: white band between black lines, frame to frame, Anton capitals; the active tab is a gold flag with white text (like 推し), hover = gold text.
4. **Title band** = the 推し FAVORITES bar, directly under the tabs (they share a line, like the profile's stacked bars; a gap there became an empty boxed-in strip): frame to frame, gold flag with a Japanese label against the left frame line + the English tab title (same visible height, measured), stats/filter links on the right. MAL's STATS drawer opens under it, also frame to frame.
5. **Sort bar**: "▸ SORT" (MAL blue) + MAL's sort links in mono capitals.
6. **Entries = poster cards like TOP ANIME**: 6 per row, 152px black-framed covers with the soft offset shadow and sheen, gold number badge with white digits (01, 02 …), a coloured strip along the bottom of the cover for the status, a white ★ score chip (hidden when unscored), title in black mono capitals (wraps, never cut), then type · progress (or CH · VOL for manga) in gray. Edit/Add · More appear on hover.
7. **Footer** = the profile's quote bar (`footer.png`) across the whole page, mirroring the header: gold dashed rule on top, black line at the bottom where the frame lines stop. Then MAL's own footer, made quiet.

Status strip colours: watching/reading **green** `#22c55e` · completed **MAL blue** `#2e51a2` · on hold **gold** · dropped **gray** `#6b7180` (red stays retired) · plan to watch/read **light gray** `#c3c8d2`.

| Tab | Japanese label | Reading | Meaning |
|---|---|---|---|
| All Anime | 鑑賞記録 | kanshō kiroku | viewing log (same as TOP ANIME) |
| All Manga | 読書記録 | dokusho kiroku | reading log (same as TOP MANGA) |
| Currently Watching | 視聴中 | shichō-chū | watching now |
| Currently Reading | 読書中 | dokusho-chū | reading now |
| Completed (anime) | 完走 | kansō | finished the run |
| Completed (manga) | 読了 | dokuryō | finished reading |
| On Hold | 保留 | horyū | on hold |
| Dropped | 中断 | chūdan | stopped |
| Plan to Watch | 視聴予定 | shichō yotei | planned viewing |
| Plan to Read | 読書予定 | dokusho yotei | planned reading |

Decided against / later: a **rows** version (compact rows with small covers) — MAL pages can only show one look and CSS can't add a switch, so it would replace the grid for everyone (or need a personal bookmark link); skipped for now (Oct 5, 2026).
