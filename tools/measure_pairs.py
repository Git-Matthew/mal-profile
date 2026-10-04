"""Measure the real ink height/position of each Japanese + English text pair in a rendered profile.html.
usage: python3 measure.py path/to/profile.html     (numbers are CSS px)"""
import io, json, sys
from PIL import Image
from playwright.sync_api import sync_playwright

PAIRS = {  # name: (japanese selector, english selector)
    "hero motto": (".title .jpn", ".title .en"),
    "favorites bar": (".band .flag", ".band .lbl"),
    "top anime": (".rowlabel >> nth=0 >> .jp2", ".rowlabel >> nth=0 >> .en2"),
    "top manga": (".rowlabel >> nth=1 >> .jp2", ".rowlabel >> nth=1 >> .en2"),
    "footer": (".foot .jpq", ".foot .enq"),
}
JS_RECT = """(el) => {
  // footer quote: measure only the characters between the brackets (「 」 and ！ stick out further)
  if (el.classList.contains('jpq')) {
    const t = el.firstChild, s = t.textContent; const r = document.createRange();
    let a = 0, b = s.length; if ('「『'.includes(s[0])) a = 1; while (b > a && '」』！!'.includes(s[b - 1])) b--;
    r.setStart(t, a); r.setEnd(t, b); const q = r.getBoundingClientRect();
    return {x: q.x, y: q.y, w: q.width, h: q.height};
  }
  // text-only box (padding excluded) for the flag block
  const r = document.createRange(); r.selectNodeContents(el); const q = r.getBoundingClientRect();
  return {x: q.x, y: q.y, w: q.width, h: q.height};
}"""


def ink_rows(img, box, color, scale=2):
    """Rows holding the element's own text colour (pixels at least ~65% of the way from background to text colour)."""
    from collections import Counter
    x, y, w, h = (round(v * scale) for v in (box["x"], box["y"], box["w"], box["h"]))
    pad = 2 * scale
    crop = img.crop((x, y - pad, x + w, y + h + pad)).convert("RGB")
    px = crop.load(); W, H = crop.size
    bg = Counter(list(crop.getdata())).most_common(1)[0][0]
    d = lambda a, b: sum((i - j) ** 2 for i, j in zip(a, b)) ** .5
    lim = 0.35 * d(color, bg)
    rows = [j for j in range(H) if any(d(px[i, j], color) < lim for i in range(W))]
    if not rows:
        return None
    top, bot = rows[0] + (y - pad), rows[-1] + (y - pad)
    return {"top": top / scale, "bottom": (bot + 1) / scale, "h": (bot + 1 - top) / scale}


def main(path):
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 798, "height": 1200}, device_scale_factor=2)
        pg.goto("file://" + path); pg.wait_for_timeout(800)
        img = Image.open(io.BytesIO(pg.screenshot(full_page=True)))
        out = {}
        for name, (js, en) in PAIRS.items():
            rj = pg.locator(js).first.evaluate(JS_RECT); re_ = pg.locator(en).first.evaluate(JS_RECT)
            col = lambda sel: tuple(int(v) for v in pg.locator(sel).first.evaluate("e => getComputedStyle(e).color").replace("rgba(", "").replace("rgb(", "").replace(")", "").split(",")[:3])
            mj, me = ink_rows(img, rj, col(js)), ink_rows(img, re_, col(en))
            fj = pg.locator(js).first.evaluate("e => getComputedStyle(e).fontSize")
            fe = pg.locator(en).first.evaluate("e => getComputedStyle(e).fontSize")
            out[name] = {"jp": {**mj, "font": fj}, "en": {**me, "font": fe},
                         "height_diff": round(me["h"] - mj["h"], 2), "top_diff": round(me["top"] - mj["top"], 2),
                         "bottom_diff": round(me["bottom"] - mj["bottom"], 2)}
        edge = pg.evaluate("() => { const t = document.querySelector('.title .en').getBoundingClientRect(); const n = document.querySelector('.nameplate'); return [t.right, n ? n.getBoundingClientRect().left : null, document.querySelector('.doc').getBoundingClientRect().height]; }")
        b.close()
    print(f"hero English ends at x={edge[0]:.0f}px, name tag starts at x={edge[1]:.0f}px, image height={edge[2]:.0f}px")
    for k, v in out.items():
        print(f"{k:14s} JP h={v['jp']['h']:5.1f} ({v['jp']['font']:>6s}) top={v['jp']['top']:7.1f} | "
              f"EN h={v['en']['h']:5.1f} ({v['en']['font']:>6s}) top={v['en']['top']:7.1f} | "
              f"Δh={v['height_diff']:+5.1f} Δtop={v['top_diff']:+5.1f} Δbottom={v['bottom_diff']:+5.1f}")
    json.dump(out, open(path + ".measure.json", "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
