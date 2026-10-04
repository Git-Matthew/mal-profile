#!/usr/bin/env python3
"""
MAL Profile Kit — build.py
Rebuilds the MyAnimeList "About Me" image from config.json.

  python build.py                       fetch live stats + posters from MAL, render output/<basename>.png
  python build.py --offline             no network: reuse data/lists_cache.json and cached posters
  python build.py --refresh-posters     re-download poster art even if cached
  python build.py --stats               only print the current stats (no render)
  python build.py --no-render           build output/profile.html but skip the PNG
  python build.py --config test.json    try a variant without touching config.json
  python build.py --no-archive          preview: don't save a dated copy into versions/
  python build.py find "Chainsaw Man" --type manga      look up MAL ids for config.json

Needs: Python 3.8+, Pillow (pip install pillow), and any Chromium-based browser
(Chrome, Edge, Chromium, or Playwright's Chromium). Set CHROME_PATH to force one.
"""
import argparse, datetime, glob, html, json, os, re, shutil, subprocess, sys, time
import urllib.parse, urllib.request
from pathlib import Path
from string import Template

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from PIL import Image, ImageChops
except ImportError:
    sys.exit("Pillow is missing. Run:  pip install pillow")

ROOT = Path(__file__).resolve().parent
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
DOC_W = 794          # inner width of the 798px card (2px border each side)
HEADER_H = 63        # 5px gold edge + 58px header bar
STATUS = {1: "watching/reading", 2: "completed", 3: "on hold", 4: "dropped", 6: "plan to watch/read"}


# ----------------------------------------------------------------- helpers
def load_config(path=None):
    def strip(o):
        if isinstance(o, dict):
            return {k: strip(v) for k, v in o.items() if not k.startswith("_")}
        if isinstance(o, list):
            return [strip(v) for v in o]
        return o
    cfg = strip(json.loads(Path(path or ROOT / "config.json").read_text(encoding="utf-8")))
    # The MAL username is kept OUT of config.json because the GitHub repo is public. It comes from the
    # MAL_USERNAME environment variable (a hidden repo secret on GitHub) or from local_settings.json
    # (only in the local copy of the kit).
    user = os.environ.get("MAL_USERNAME", "").strip()
    local = ROOT / "local_settings.json"
    if not user and local.exists():
        user = str(json.loads(local.read_text(encoding="utf-8")).get("mal_username", "")).strip()
    cfg["mal_username"] = user or str(cfg.get("mal_username", "")).strip()
    hero = cfg.setdefault("hero", {})
    if not str(hero.get("display_name", "")).strip():   # empty = show the MAL username in capitals
        hero["display_name"] = cfg["mal_username"].upper()
    return cfg


def http_get(url, binary=False, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read()
            return data if binary else data.decode("utf-8", "replace")
        except Exception as e:  # noqa
            last = e
            time.sleep(1.5 * (i + 1))
    curl = shutil.which("curl")
    if curl:  # fallback: some networks/proxies behave better with curl
        p = subprocess.run([curl, "-sSL", "-m", "40", "-A", UA, url], capture_output=True)
        if p.returncode == 0 and p.stdout:
            return p.stdout if binary else p.stdout.decode("utf-8", "replace")
    raise RuntimeError(f"Download failed: {url}  ({last})")


def esc(s):
    return html.escape(str(s), quote=False)


def fmt(v):
    return f"{v:,}" if isinstance(v, int) else str(v)


# ----------------------------------------------------------------- MAL data
def fetch_list(user, kind):
    items, off = [], 0
    while True:
        url = f"https://myanimelist.net/{kind}list/{urllib.parse.quote(user)}/load.json?status=7&offset={off}"
        page = json.loads(http_get(url))
        if not page:
            break
        items += page
        off += 300
        if len(page) < 300:
            break
        time.sleep(1.2)
    return items


def get_lists(cfg, offline):
    cache = ROOT / "data" / "lists_cache.json"
    if not offline:
        try:
            data = {"fetched": datetime.datetime.now().isoformat(timespec="seconds"),
                    "anime": fetch_list(cfg["mal_username"], "anime"),
                    "manga": fetch_list(cfg["mal_username"], "manga")}
            cache.parent.mkdir(exist_ok=True)
            cache.write_text(json.dumps(data), encoding="utf-8")
            return data
        except Exception as e:
            print(f"! Could not reach MAL ({e}). Falling back to cached list data.")
    if not cache.exists():
        sys.exit("No cached list data yet (data/lists_cache.json). Run once with internet access.")
    data = json.loads(cache.read_text(encoding="utf-8"))
    print(f"  using cached list data from {data.get('fetched', '?')}")
    return data


def compute_stats(anime, manga, rules):
    A = rules.get("anime_statuses", [2])
    M = rules.get("manga_statuses", [1, 2])
    MS = rules.get("mean_from_statuses", [2])
    a_sel = [a for a in anime if a.get("status") in A]
    m_sel = [m for m in manga if m.get("status") in M]
    scored = [a["score"] for a in anime if a.get("status") in MS and (a.get("score") or 0) > 0]
    n = lambda lst, st: len([x for x in lst if x.get("status") == st])
    return {
        "mean_score": f"{sum(scored) / len(scored):.2f}" if scored else "—",
        "anime_completed": n(anime, 2),
        "anime_episodes": sum(int(a.get("num_watched_episodes") or 0) for a in a_sel),
        "anime_watching": n(anime, 1),
        "anime_plan_to_watch": n(anime, 6),
        "anime_total_entries": len(anime),
        "manga_volumes": sum(int(m.get("num_read_volumes") or 0) for m in m_sel),
        "manga_chapters": sum(int(m.get("num_read_chapters") or 0) for m in m_sel),
        "manga_titles": len(m_sel),
        "manga_completed": n(manga, 2),
        "manga_reading": n(manga, 1),
        "manga_total_entries": len(manga),
    }


def poster(kind, mal_id, refresh=False, offline=False):
    p = ROOT / "assets" / "posters" / f"{kind}_{mal_id}.jpg"
    if p.exists() and p.stat().st_size > 1500 and not refresh:
        return p
    if offline:
        sys.exit(f"Missing cached poster for {kind} {mal_id} and --offline was set.")
    page = http_get(f"https://myanimelist.net/{kind}/{mal_id}")
    m = re.search(r'<meta property="og:image" content="([^"]+)"', page)
    if not m:
        sys.exit(f"Couldn't find poster art for {kind} id {mal_id}. Is the id right?")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(http_get(m.group(1), binary=True))
    time.sleep(0.6)
    return p


def find(query, kind, limit=6):
    page = http_get(f"https://myanimelist.net/{kind}.php?q={urllib.parse.quote_plus(query)}&cat={kind}")
    ids = []
    for mid in re.findall(rf'https://myanimelist\.net/{kind}/(\d+)/', page):
        if mid not in ids:
            ids.append(mid)
    print(f'\nMAL {kind} results for "{query}":\n')
    for mid in ids[:limit]:
        p = http_get(f"https://myanimelist.net/{kind}/{mid}")
        t = re.search(r'<meta property="og:title" content="([^"]+)"', p)
        ty = re.search(r'Type:</span>\s*(?:<a[^>]*>)?([^<\n]+)', p)
        en = re.search(r'English:</span>\s*([^<\n]+)', p)
        print(f"  mal_id {mid:>7}  | {html.unescape(t.group(1)) if t else '?'}"
              f"  | type: {ty.group(1).strip() if ty else '?'}"
              f"  | english: {html.unescape(en.group(1).strip()) if en else '-'}")
        time.sleep(0.6)
    print("\nCopy the right mal_id into config.json (favorites.anime / favorites.manga).")


# ----------------------------------------------------------------- page assembly
def font_faces():
    f = ROOT / "assets" / "fonts"
    faces = [("KitAnton", "Anton-Regular.ttf", "400"), ("KitOswald", "Oswald-Variable.ttf", "200 700"),
             ("KitMono", "ShareTechMono-Regular.ttf", "400"), ("KitJP", "NotoSansJP-Variable.ttf", "100 900")]
    css = [f'  @font-face{{font-family:"{n}";src:url("{(f / fn).as_uri()}");font-weight:{w};}}' for n, fn, w in faces]
    # Symbols like ★ and ▸ aren't in Anton/Oswald/Share Tech Mono. Pin them to the bundled DejaVu Sans so the
    # image looks identical on every machine (Claude's sandbox, GitHub Actions, Windows + Edge).
    # (Same weight as each family's main face, so a bold label still gets its letters from the main font.)
    sym = (f / "DejaVuSans.ttf").as_uri()
    css += [f'  @font-face{{font-family:"{n}";src:url("{sym}");font-weight:{w};'
            f'unicode-range:U+2190-21FF,U+25A0-25FF,U+2600-27BF;}}' for n, _, w in faces[:3]]
    return "\n".join(css)


def card(rank, img_path, caption, cls):
    return (f'        <div class="{cls}"><div class="pw"><div class="rk">{rank:02d}</div>'
            f'<img src="{img_path.as_uri()}"><div class="sheen"></div></div><div class="cap">{esc(caption)}</div></div>')


def build_html(cfg, stats, posters):
    ch = cfg["character"]
    img_path = (ROOT / ch["image"]).resolve()
    w, h = Image.open(img_path).size
    img_left = DOC_W - ch["right_px"] - w * ch["height_px"] / h          # where the art's left edge lands
    anime, manga = cfg["favorites"]["anime"], cfg["favorites"]["manga"]
    if len(anime) > 5 or len(manga) > 5:
        sys.exit("Max 5 anime and 5 manga (a 6th won't fit the 798px width).")
    mode = "side" if len(manga) <= 3 else "full"
    hero_h = 250 if mode == "side" else 236
    poster_h = 198 if mode == "side" else 184
    band_top = HEADER_H + hero_h

    hd = cfg["header"]
    stars_html = (f'<span class="sep">//</span><span class="st">{"★" * hd["stars"]}</span>' if hd.get("stars") else "")
    hero = cfg["hero"]
    chips = [f'          <span class="chip"><span class="dot"></span> STATUS: {esc(hero["status_text"])}</span>']
    if hero.get("show_mean_score_chip", True):
        chips.append(f'          <span class="chip">MEAN SCORE <span class="star">★</span> {stats["mean_score"]}</span>')
    tag = ch.get("name_tag", {})
    nameplate = ""
    if tag.get("enabled"):
        star = '<span class="st">★</span>' if tag.get("show_star", True) else ""
        nameplate = (f'      <div class="nameplate" style="left:{round(img_left - 11.5)}px;top:{tag.get("top_px", 64)}px">'
                     f'{star}<span class="nm">{esc(tag["text_jp"])}</span></div>')

    st = cfg["stats"]
    rows = []
    for r in st["rows"]:
        v = fmt(stats.get(r["value"], "?"))
        sfx = f'<small>{esc(r["suffix"])}</small>' if r.get("suffix") else ""
        rows.append((esc(r["label"]), v, sfx))
    anime_cards = "\n".join(card(i + 1, posters[("anime", a["mal_id"])], a["caption"], "card") for i, a in enumerate(anime))
    if mode == "side":
        mcards = "\n".join(card(i + 1, posters[("manga", m["mal_id"])], m["caption"], "mcard") for i, m in enumerate(manga))
        srows = "\n".join(f'            <div class="srow"><span class="k">{k}</span><span class="v">{v}{s}</span></div>' for k, v, s in rows)
        manga_block = (f'      <div class="mrow">\n{mcards}\n        <div class="statcard">\n'
                       f'          <div class="sh">{esc(st["title"])}</div>\n          <div class="stars">{"★" * st.get("stars", 5)}</div>\n'
                       f'          <div class="srows">\n{srows}\n          </div>\n        </div>\n      </div>')
    else:
        mcards = "\n".join(card(i + 1, posters[("manga", m["mal_id"])], m["caption"], "card") for i, m in enumerate(manga))
        items = "".join(f'<div class="it"><span class="k">{k}</span><span class="v">{v}{s}</span></div>' for k, v, s in rows)
        manga_block = (f'      <div class="row">\n{mcards}\n      </div>\n'
                       f'      <div class="statstrip"><span class="sh">{esc(st["title"])}</span>'
                       f'<span class="stars">{"★" * st.get("stars", 5)}</span><div class="sitems">{items}</div></div>')

    th = cfg.get("theme", {})
    theme_classes = ""
    for key, cls in (("header_bar", "hdr-light"), ("favorites_bar", "band-light"),
                     ("stats_box", "stats-light"), ("footer_bar", "foot-light")):
        v = str(th.get(key, "dark")).lower()
        if v not in ("dark", "light"):
            sys.exit(f'config.json theme.{key} must be "dark" or "light" (got "{v}")')
        if v == "light":
            theme_classes += " " + cls
    if str(th.get("stats_labels", "gray")).lower() == "black":
        theme_classes += " stats-ink"      # white stats box only: black labels instead of gray
    if str(th.get("captions", "gray")).lower() == "black":
        theme_classes += " caps-ink"       # titles under the covers in black instead of gray

    fs, c = cfg["favorites_section"], cfg["colors"]
    tpl = Template((ROOT / "template" / "profile_template.html").read_text(encoding="utf-8"))
    return tpl.substitute(
        FONT_FACES=font_faces(), INK=c["ink"], GOLD=c["gold"], BLUE=c["blue"], GREEN=c["green"],
        POSTER_H=poster_h, HERO_H=hero_h, BAND_TOP=band_top, MODE=mode, THEME_CLASSES=theme_classes,
        CLIP=f"polygon(0 0,100% 0,100% {band_top}px,0 {band_top}px)",
        CHAR_SRC=img_path.as_uri(), CHAR_H=ch["height_px"], CHAR_TOP=ch["top_px"], CHAR_RIGHT=ch["right_px"],
        CREST=esc(hd["crest_kanji"]), HEADER_TITLE=esc(hd["title"]), HEADER_NUMBER=esc(hd["number"]), HEADER_STARS_HTML=stars_html,
        NAMEPLATE_HTML=nameplate, DISPLAY_NAME=esc(hero["display_name"]), TAGLINE_JP=esc(hero["tagline_jp"]),
        TAGLINE_EN=esc(hero["tagline_en"]), CHIPS_HTML="\n".join(chips),
        FLAG_JP=esc(fs["flag_jp"]), FAV_TITLE=esc(fs["title"]),
        ANIME_LABEL=esc(fs["anime_label"]), ANIME_LABEL_JP=esc(fs["anime_label_jp"]), ANIME_CARDS=anime_cards,
        MANGA_LABEL=esc(fs["manga_label"]), MANGA_LABEL_JP=esc(fs["manga_label_jp"]), MANGA_BLOCK=manga_block,
        QUOTE_JP=esc(cfg["footer_quote"]["jp"]), QUOTE_EN=esc(cfg["footer_quote"]["en"]),
    ), mode


# ----------------------------------------------------------------- rendering
def find_browser():
    cands = [os.environ.get("CHROME_PATH")]
    cands += sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))
    cands += sorted(glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux/chrome")))
    cands += [shutil.which(x) for x in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "microsoft-edge", "msedge")]
    cands += [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    for c in cands:
        if c and os.path.exists(c):
            return c
    sys.exit("No Chromium-based browser found. Install Chrome/Edge or set CHROME_PATH to one.")


def render(html_path, png_path):
    shot = png_path.with_suffix(".raw.png")
    subprocess.run([find_browser(), "--headless=new", "--disable-gpu", "--no-sandbox", "--allow-file-access-from-files",
                    "--hide-scrollbars", "--force-device-scale-factor=2", "--window-size=798,1200",
                    "--virtual-time-budget=8000", f"--screenshot={shot}", html_path.as_uri()],
                   capture_output=True, timeout=180)
    if not shot.exists():
        sys.exit("The browser didn't produce a screenshot. Try setting CHROME_PATH to a different Chromium/Chrome/Edge.")
    im = Image.open(shot).convert("RGB")
    bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    if bbox:
        im = im.crop(bbox)
    im.save(png_path, optimize=True)
    shot.unlink()
    return im.size


# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Rebuild the MAL About Me image from config.json")
    ap.add_argument("cmd", nargs="?", default="build", choices=["build", "find"])
    ap.add_argument("query", nargs="?")
    ap.add_argument("--type", default="anime", choices=["anime", "manga"])
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--refresh-posters", action="store_true")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--config", help="use a different config file (for experiments)")
    ap.add_argument("--no-archive", action="store_true", help="don't save a dated copy into versions/ (for previews)")
    a = ap.parse_args()

    if a.cmd == "find":
        if not a.query:
            sys.exit('Usage: python build.py find "title" --type anime|manga')
        return find(a.query, a.type)

    cfg = load_config(a.config)
    if not cfg["mal_username"]:
        sys.exit('No MAL username. Set the MAL_USERNAME environment variable (GitHub: repo secret), or create '
                 'local_settings.json next to build.py containing: {"mal_username": "YourName"}')
    print("MAL Profile Kit — building")
    lists = get_lists(cfg, a.offline)
    stats = compute_stats(lists["anime"], lists["manga"], cfg["stats"]["rules"])
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    print("  stats: " + " | ".join(f"{k}={fmt(v)}" for k, v in stats.items()))
    if a.stats:
        return

    posters = {}
    for kind in ("anime", "manga"):
        for item in cfg["favorites"][kind]:
            posters[(kind, item["mal_id"])] = poster(kind, item["mal_id"], a.refresh_posters, a.offline)
    print(f"  posters ready: {len(posters)}")

    html_text, mode = build_html(cfg, stats, posters)
    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    html_path = out / "profile.html"
    html_path.write_text(html_text, encoding="utf-8")
    (out / "about_me_bbcode.txt").write_text(
        "GitHub Actions publishes this image to a permanent link:\n"
        "  https://raw.githubusercontent.com/<github-user>/<repo>/live/" + cfg["output"]["basename"] + ".png\n"
        "MAL > Settings > About Me Style = Classic > About Me (Classic) only needs this once:\n\n"
        "[center][img]IMAGE_URL[/img][/center]\n", encoding="utf-8")
    if a.no_render:
        print(f"  wrote {html_path} (render skipped)")
        return

    png = out / f"{cfg['output']['basename']}.png"
    w, h = render(html_path, png)
    if not a.no_archive:
        stamp = datetime.date.today().isoformat()
        (ROOT / "versions").mkdir(exist_ok=True)
        shutil.copy2(png, ROOT / "versions" / f"{stamp}_{cfg['output']['basename']}.png")
    dh = h // 2
    print(f"  layout: manga '{mode}' mode | rendered {w}x{h}px (shows on MAL at {w // 2}x{dh})")
    if dh > cfg["output"].get("max_height_px", 1000):
        print(f"! WARNING: {dh}px tall — MAL hides anything past 1000px behind 'Read More'. "
              "Shorten captions, drop a stats row, or reduce character/hero sizes.")
    print(f"  done -> {png}\n  next: upload it, then use output/about_me_bbcode.txt")


if __name__ == "__main__":
    main()
