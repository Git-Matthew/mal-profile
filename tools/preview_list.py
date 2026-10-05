"""Preview the anime/manga list design on the REAL MAL list pages, before anything is published.

  python3 tools/preview_list.py                          anime + manga list, top of page
  python3 tools/preview_list.py "animelist?status=2"     any list view (status=1 watching/reading, 2 completed, 6 plan to)
  python3 tools/preview_list.py --measure                also check every Japanese + English pair (banner title + title band)

Run `python3 build.py --offline` first. The GitHub Pages URLs are answered from output/list/, and MAL's one-line custom
CSS is injected exactly where MAL puts it (<style id="custom-css"> after the theme CSS). Screenshots go to output/list_preview/.
Needs Playwright + Chromium (Claude's sandbox has both). The list must be public."""
import io, math, mimetypes, sys
from collections import Counter
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT))
import build  # noqa: E402

cfg = build.load_config()
BASE = cfg.get("lists", {}).get("pages_url", "https://git-matthew.github.io/mal-profile/list/")
CUSTOM = f'@\\import "{BASE}list.css";'
OUT = KIT / "output" / "list_preview"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
MEASURE = "--measure" in sys.argv
pages = args or ["animelist", "mangalist"]
if MEASURE and not args:
    pages = ["animelist", "animelist?status=1", "animelist?status=2", "animelist?status=6", "mangalist", "mangalist?status=1", "mangalist?status=2"]


def serve(route):
    f = KIT / "output" / "list" / route.request.url.split(BASE, 1)[1].split("?")[0]
    route.fulfill(status=200 if f.exists() else 404, body=f.read_bytes() if f.exists() else b"",
                  headers={"content-type": mimetypes.guess_type(str(f))[0] or "text/css", "access-control-allow-origin": "*"})


def ink(img, box, color, bg, scale=2):
    """top/bottom (CSS px) of the rows that hold `color` text inside box."""
    x, y, w, h = (round(v * scale) for v in box)
    crop = img.crop((x, y, x + w, y + h)).convert("RGB"); px = crop.load()
    lim = 0.5 * math.dist(color, bg)
    rows = [j for j in range(crop.size[1]) if any(math.dist(px[i, j], color) < lim for i in range(crop.size[0]))]
    return (rows[0] / scale + box[1], (rows[-1] + 1) / scale + box[1]) if rows else None


OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1280, "height": 1000}, device_scale_factor=2)
    ctx.route(BASE + "**", serve)
    pg = ctx.new_page()
    for spec in pages:
        kind, _, q = spec.partition("?")
        pg.goto(f"https://myanimelist.net/{kind}/{cfg['mal_username']}" + (f"?{q}" if q else ""), wait_until="domcontentloaded", timeout=90000)
        pg.evaluate("""css => { const s = document.createElement('style'); s.id = 'custom-css'; s.textContent = css;
                         const t = document.querySelector('head style'); t ? t.after(s) : document.head.appendChild(s); }""", CUSTOM)
        try:
            pg.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        pg.wait_for_timeout(2500)
        # a brand-new (US) visitor gets MAL's privacy pop-up: hide it for the screenshot
        pg.add_style_tag(content='#qc-cmp2-container,.qc-cmp2-container,[id^="qc-cmp"],.fc-consent-root,#onetrust-consent-sdk,'
                                 'div[class*="consent"],div[id*="consent"]{display:none !important}')
        pg.evaluate("""() => { for (const e of document.querySelectorAll('body > div')) { const s = getComputedStyle(e);
            if (s.position === 'fixed' && +s.zIndex > 1000 && e.innerText.includes('Personal Information')) e.remove(); } }""")
        pg.wait_for_timeout(300)
        name = spec.replace("?", "_").replace("=", "")
        pg.screenshot(path=str(OUT / f"{name}.png"))
        print(f"  {spec}: output/list_preview/{name}.png")
        if MEASURE:
            band = pg.eval_on_selector(".list-status-title", "e => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height]; }")
            txt = pg.eval_on_selector(".list-status-title .text", "e => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height, e.textContent.trim()]; }")
            img = Image.open(io.BytesIO(pg.screenshot()))
            j = ink(img, [band[0], band[1] + 3, txt[0] - band[0], band[3] - 6], (255, 255, 255), (215, 167, 54))     # white kanji on the gold flag
            fg = (21, 21, 28) if pg.evaluate("getComputedStyle(document.querySelector('.list-status-title .text')).color") != "rgb(255, 255, 255)" else (255, 255, 255)
            bgc = (255, 255, 255) if fg == (21, 21, 28) else (21, 21, 28)
            e = ink(img, [txt[0] + 1, band[1] + 3, txt[2] - 2, band[3] - 6], fg, bgc)
            print(f"    title band '{txt[4]}': JP h={j[1]-j[0]:.1f}  EN h={e[1]-e[0]:.1f}  (keep within 1px)")
    if MEASURE:   # banner title pair, measured on the banner art itself
        ch, hd, c = cfg["character"], cfg["header"], cfg["colors"]
        from string import Template
        tpl = Template((KIT / "template" / "list_assets_template.html").read_text(encoding="utf-8"))
        bp = b.new_page(viewport={"width": 1060, "height": 330}, device_scale_factor=2)
        for kind in ("anime", "manga"):
            lc = cfg.get("lists", {}).get(kind, {})
            html = tpl.substitute(FONT_FACES=build.font_faces(), INK=c["ink"], GOLD=c["gold"], BLUE=c["blue"], GREEN=c["green"], PAD=18,
                                  BODY_CLASSES=build.name_class(cfg), CHAR_SRC="", CHAR_H=1, CHAR_TOP=0, CHAR_RIGHT=0, NAMEPLATE_HTML="",
                                  DISPLAY_NAME="X", CREST="", HEADER_TITLE="", HEADER_NUMBER="", HEADER_STARS_HTML="", QUOTE_JP="", QUOTE_EN="",
                                  POP=build.LIST_POP, TITLE_JP=lc.get("title_jp", ""), TITLE_EN=lc.get("title_en", ""), CHIPS_HTML="",
                                  PART="banner", W=build.LIST_W, H=build.LIST_POP + build.LIST_HERO_H)
            f = OUT / "_measure.html"; f.write_text(html, encoding="utf-8"); bp.goto(f.as_uri()); bp.wait_for_timeout(600)
            img = Image.open(io.BytesIO(bp.screenshot()))
            r = lambda sel: bp.eval_on_selector(sel, "e => { const q = e.getBoundingClientRect(); return [q.x, q.y - 4, q.width, q.height + 8]; }")
            j = ink(img, r(".title .jpn"), (215, 167, 54), (255, 255, 255)); e = ink(img, r(".title .en"), (112, 120, 132), (255, 255, 255))
            print(f"  banner title ({kind}): JP h={j[1]-j[0]:.1f}  EN h={e[1]-e[0]:.1f}  top JP={j[0]:.1f} EN={e[0]:.1f}  (keep within 1px)")
            f.unlink()
    b.close()
