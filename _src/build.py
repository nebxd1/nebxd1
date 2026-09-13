#!/usr/bin/env python3
"""Builds the Filmbot-inspired SVG artwork used by the nebxd1 profile README.

Edit PROFILE below, then run:

    pip install fonttools
    python _src/build.py

Every SVG in ../assets is regenerated. Text is converted to vector outlines
(Barlow Condensed + JetBrains Mono, both OFL — see _src/fonts), so it looks the
same on every device without loading any fonts.
"""
import html
import random
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

SRC = Path(__file__).resolve().parent
OUT = SRC.parent / "assets"

# ---------------------------------------------------------------- content ---
PROFILE = {
    "handle": "NEBXD1",
    "ticker": [
        "Building a movie website — showtimes, tickets & film series",
        "Open to collaborations on film & cinema projects",
        "Currently watching: everything at the local indie theater",
    ],
    "ticker_buttons": ["REPOSITORIES", "CONTACT"],
    "hero": {
        "kicker": "CODE FOR THE NEW ERA OF",
        "title": ["MOVIE", "WEBSITES"],
        "sub": "More than a developer — your collaborator.",
    },
    "about": {
        "lead": "This is a time of rebirth for film culture on the web.",
        "rest": "I design and build bold, fast websites for the theaters, festivals "
                "and film lovers leading the way — from showtimes to checkout.",
        "caption": "CRAFTED WITH CARE FOR THOSE WHO LOVE THE BIG SCREEN",
        "tags": ["BUILD FOR THE WEB", "IMPRESS THE AUDIENCE"],
    },
    "skills": {
        "kicker": "TOOLKIT",
        "title": ["SEAMLESS", "SUITE OF", "SKILLS"],
        "body": "By listening closely and sweating the details, I find better ways "
                "to build — easing workflows and elevating the audience experience.",
        "columns": {
            "CORE STACK": ["HTML5", "CSS3 / SASS", "JAVASCRIPT", "TYPESCRIPT",
                           "REACT", "NODE.JS", "PYTHON", "GIT & GITHUB"],
            "ALSO WORKING WITH": ["WEBFLOW", "BLENDER / 3D", "FIGMA",
                                  "RESPONSIVE UI", "ACCESSIBILITY", "VIDEO & MOTION"],
        },
    },
    "stats": {
        "kicker": "BY THE NUMBERS",
        "title": ["WHERE THE", "HOURS GO"],
        "body": "More time in the editor than the cinema — but not by much.",
        "bars": [("WRITING CODE", 55), ("WATCHING FILMS", 35), ("EVERYTHING ELSE", 10)],
        "footnote": "*2026 self-reported, highly unscientific survey [NEBXD1]",
    },
    "projects": [
        {"file": "project-01", "label": "Now Showing", "num": "(01)",
         "title": ["MOVIE", "WEBSITE"],
         "body": "A home for showtimes, tickets and film series — designed and "
                 "built from scratch.",
         "cta": "VIEW REPOSITORY", "caption": "MOVIE WEBSITE", "art": "cinema"},
        {"file": "project-02", "label": "Coming Soon", "num": "(02)",
         "title": ["NEXT", "FEATURE"],
         "body": "Something new is in pre-production. Follow along to catch "
                 "the premiere.",
         "cta": "FOLLOW ALONG", "caption": "IN PRODUCTION", "art": "leader"},
    ],
    "contact": {
        "title": ["LET’S BUILD", "TOGETHER"],
        "kicker": "MORE THAN A DEVELOPER",
        "body": "Got a cinema, festival or film project that needs a home online? "
                "Open an issue, drop a message, or find me in the credits.",
        "cta": "GET IN TOUCH",
        "sign": ["NOW PLAYING", "YOUR", "PROJECT"],
        "caption": "THE MARQUEE",
    },
    "footer": {
        "left": "© 2026 NEBXD1",
        "mid": "MOVIES NEVER DIE",
        "right": "GITHUB.COM/NEBXD1",
    },
}

# ------------------------------------------------------------------ style ---
W = 1000
INK, PAPER, RED = "#0C0C0C", "#F9F8F8", "#FF4040"
G900, G800, G700, G500, G400, G300 = "#171717", "#202020", "#494949", "#797979", "#9B9B9B", "#CBCBCB"

BASE_CSS = """
.rise{animation:rise 1.2s cubic-bezier(.16,1,.3,1) both}
@keyframes rise{from{transform:translateY(180px)}}
.fade{animation:fade 1s ease both}
@keyframes fade{from{opacity:0}}
.up{animation:up 1s cubic-bezier(.16,1,.3,1) both}
@keyframes up{from{opacity:0;transform:translateY(14px)}}
"""


class Font:
    """A font whose glyphs are drawn as SVG outlines.

    GitHub serves repo images under a CSP that can block embedded web fonts, so
    all text is converted to paths at build time and renders identically everywhere.
    """

    def __init__(self, key, filename, wght=None):
        tt = TTFont(SRC / "fonts" / filename)
        if wght is not None and "fvar" in tt:
            tt = instantiateVariableFont(tt, {"wght": wght})
        self.key = key
        self.tt = tt
        self.glyphs = tt.getGlyphSet()
        self.upm = tt["head"].unitsPerEm
        self.cmap = tt.getBestCmap()
        self.adv = {g: m[0] for g, m in tt["hmtx"].metrics.items()}

    def glyph(self, ch):
        name = self.cmap.get(ord(ch))
        if name is None:
            raise ValueError(f"{self.key} has no glyph for {ch!r}")
        return name

    def width(self, text, size, ls=0.0):
        units = sum(self.adv[self.glyph(ch)] for ch in text)
        return units / self.upm * size + ls * max(len(text) - 1, 0)

    def path(self, name):
        pen = SVGPathPen(self.glyphs, ntos=lambda v: f"{v:.0f}")
        self.glyphs[name].draw(pen)
        return pen.getCommands()


BOLD = Font("b", "BarlowCondensed-Bold.ttf")
MED = Font("m", "BarlowCondensed-Medium.ttf")
MONO_B = Font("mb", "JetBrainsMono.ttf", wght=700)
MONO = Font("mr", "JetBrainsMono.ttf", wght=400)


def esc(s):
    return html.escape(s, quote=True)


class SVG:
    def __init__(self, name, h, title):
        self.name, self.h, self.title = name, h, title
        self.defs, self.body, self.css = [], [], [BASE_CSS]
        self.glyph_ids = {}
        self.n = 0

    def uid(self, prefix):
        self.n += 1
        return f"{prefix}{self.n}"

    def add(self, *parts):
        self.body.extend(parts)

    def glyph_ref(self, font, name):
        key = (font.key, name)
        if key not in self.glyph_ids:
            gid = f"{font.key}{font.tt.getGlyphID(name)}"
            self.glyph_ids[key] = gid
            self.defs.append(f'<path id="{gid}" d="{font.path(name)}"/>')
        return self.glyph_ids[key]

    def text(self, x, y, s, font, size, fill, anchor="start", ls=0, cls="", style=""):
        """Lay out `s` as outlined glyphs with its baseline at (x, y)."""
        if anchor == "middle":
            x -= font.width(s, size, ls) / 2
        elif anchor == "end":
            x -= font.width(s, size, ls)
        k = size / font.upm
        uses, pen = [], 0.0
        for ch in s:
            name = font.glyph(ch)
            if not ch.isspace():
                uses.append(f'<use href="#{self.glyph_ref(font, name)}" x="{pen:.0f}"/>')
            pen += font.adv[name] + ls / k
        out = (f'<g transform="translate({x:.2f} {y:.2f}) scale({k:.5f} {-k:.5f})" '
               f'fill="{fill}">{"".join(uses)}</g>')
        # Animations own `transform`, so they go on a wrapper, never on the placed group.
        if cls or style:
            c = f' class="{cls}"' if cls else ""
            st = f' style="{style}"' if style else ""
            out = f"<g{c}{st}>{out}</g>"
        return out

    def clip_rect(self, x, y, w, h, rx=0):
        cid = self.uid("c")
        self.defs.append(f'<clipPath id="{cid}"><rect x="{x:g}" y="{y:g}" width="{w:g}" '
                         f'height="{h:g}" rx="{rx:g}"/></clipPath>')
        return cid

    def render(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{self.h}" '
                f'viewBox="0 0 {W} {self.h}" role="img" aria-labelledby="t">'
                f'<title id="t">{esc(self.title)}</title>'
                f'<defs><clipPath id="card"><rect width="{W}" height="{self.h}" rx="14"/></clipPath>'
                f'{"".join(self.defs)}</defs><style>{"".join(self.css)}</style>'
                f'<g clip-path="url(#card)"><rect width="{W}" height="{self.h}" fill="{INK}"/>'
                f'{"".join(self.body)}</g></svg>')

    def save(self):
        path = OUT / f"{self.name}.svg"
        path.write_text(self.render(), encoding="utf-8")
        print(f"  {path.name:16} {path.stat().st_size / 1024:6.1f} KB")


# ---------------------------------------------------------------- helpers ---
def wrap(font, text, size, maxw):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and font.width(trial, size) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur] if cur else lines


def fit(font, lines, maxw, maxsize, ls_em=0.0):
    size = min(maxw / (font.width(l, 1) + ls_em * (len(l) - 1)) for l in lines)
    return min(maxsize, size)


def paper(d):
    d.add(f'<rect x="12" y="12" width="{W - 24}" height="{d.h - 24}" rx="10" fill="{PAPER}"/>')


def headline(d, lines, x, y, size, fill, anchor="start", delay=0.1, step=0.12, lh=0.86):
    """Big condensed caps that rise into place line by line, like Filmbot's reveals."""
    ls = -0.01 * size
    for i, line in enumerate(lines):
        base = y + i * size * lh
        cid = d.clip_rect(0, base - size * 0.82, W, size * 0.9)
        t = d.text(x, base, line, BOLD, size, fill, anchor, ls)
        d.add(f'<g clip-path="url(#{cid})"><g class="rise" style="animation-delay:{delay + i * step:.2f}s">{t}</g></g>')
    return y + (len(lines) - 1) * size * lh


def paragraph(d, text, x, y, size, fill, maxw, lh=1.3, font=MED, delay=0.5, anchor="start"):
    lines = wrap(font, text, size, maxw)
    for i, line in enumerate(lines):
        d.add(d.text(x, y + i * size * lh, line, font, size, fill, anchor, cls="up",
                     style=f"animation-delay:{delay + i * 0.06:.2f}s"))
    return y + (len(lines) - 1) * size * lh


def bracket(d, x, y, label, fill=PAPER, size=12):
    d.add(d.text(x, y, f"[ {label} ]", MONO_B, size, fill, ls=0.5))


def button(d, x, y, label, fill=RED, color=PAPER, arrow=True, size=13, h=44, pad=20):
    """Filmbot-style flat red button with a nudging arrow. (x, y) is the top-left."""
    arrow_w = MONO_B.width("→ ", size) + 6 if arrow else 0
    w = pad * 2 + arrow_w + MONO_B.width(label, size, 0.6)
    d.add(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h}" fill="{fill}"/>')
    ty = y + h / 2 + size * 0.36
    if arrow:
        d.css.append(".nudge{animation:nudge 1.6s ease-in-out infinite}"
                     "@keyframes nudge{50%{transform:translateX(4px)}}")
        d.add(f'<g class="nudge">{d.text(x + pad, ty, "→", MONO_B, size, color)}</g>')
    d.add(d.text(x + pad + arrow_w, ty, label, MONO_B, size, color, ls=0.6))
    return w


def film_icon(d, cx, y, fill=G900, s=6):
    """Small checkered clapper mark, standing in for Filmbot's pixel logo."""
    rows = ["X.X.X", ".X.X.", "X.X.X"]
    x0 = cx - len(rows[0]) * s / 2
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "X":
                d.add(f'<rect x="{x0 + c * s:g}" y="{y + r * s:g}" width="{s}" height="{s}" fill="{fill}"/>')


def grain(d, x, y, w, h, clip=None, opacity=0.14):
    fid = d.uid("g")
    d.defs.append(
        f'<filter id="{fid}" x="0" y="0" width="100%" height="100%">'
        f'<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="3">'
        f'<animate attributeName="seed" values="1;5;9;3;7" dur="0.6s" repeatCount="indefinite" calcMode="discrete"/>'
        f'</feTurbulence><feColorMatrix type="saturate" values="0"/></filter>')
    cp = f' clip-path="url(#{clip})"' if clip else ""
    d.add(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" filter="url(#{fid})" '
          f'opacity="{opacity}" style="mix-blend-mode:overlay"{cp}/>')


def motion_scene(d, x, y, w, h, seed=7, figure=True, speed=9):
    """A tracking shot: blurred city streaks pan past a runner, like Filmbot's hero video."""
    rng = random.Random(seed)
    bg = d.uid("bg")
    d.defs.append(f'<linearGradient id="{bg}" x1="0" y1="0" x2="0.3" y2="1">'
                  f'<stop offset="0" stop-color="#3b4644"/><stop offset=".55" stop-color="#202826"/>'
                  f'<stop offset="1" stop-color="#101413"/></linearGradient>')
    blur = d.uid("b")
    d.defs.append(f'<filter id="{blur}" x="-20%" y="-5%" width="140%" height="110%">'
                  f'<feGaussianBlur stdDeviation="18 7"/></filter>')
    d.add(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="url(#{bg})"/>')
    period = max(700, w * 1.6)
    palette = ["#58706b", "#8fa19b", "#2a3533", "#c8bba8", "#e9e4da", "#141a19", "#6c5a4d", "#a5b7b1"]
    streaks = []
    for _ in range(int(period / 9)):
        sx, sw = rng.uniform(0, period), rng.uniform(6, 60)
        sy, sh = y + rng.uniform(-h * 0.1, h * 0.35), rng.uniform(h * 0.4, h * 1.1)
        col, op = rng.choice(palette), rng.uniform(0.25, 0.8)
        for off in (0, period):
            streaks.append(f'<rect x="{x + sx + off - period * 0.25:.1f}" y="{sy:.1f}" width="{sw:.1f}" '
                           f'height="{sh:.1f}" fill="{col}" opacity="{op:.2f}"/>')
    pan = d.uid("pan")
    d.css.append(f".{pan}{{animation:{pan} {speed}s linear infinite}}"
                 f"@keyframes {pan}{{to{{transform:translateX(-{period:.0f}px)}}}}")
    d.add(f'<g filter="url(#{blur})"><g class="{pan}">{"".join(streaks)}</g></g>')
    if figure:
        # A runner in a white tank top, softly blurred and bobbing in stride.
        fx, fy, s = x + w * 0.46, y + h * 0.2, h / 540
        soft = d.uid("s")
        d.defs.append(f'<filter id="{soft}" x="-50%" y="-20%" width="200%" height="140%">'
                      f'<feGaussianBlur stdDeviation="{5 * s:.1f} {1.5 * s:.1f}"/></filter>')
        d.css.append(".bob{animation:bob .42s ease-in-out infinite alternate}"
                     "@keyframes bob{to{transform:translateY(7px)}}"
                     ".arm{transform-box:fill-box;transform-origin:50% 0;animation:arm .84s ease-in-out infinite alternate}"
                     "@keyframes arm{from{transform:rotate(-38deg)}to{transform:rotate(30deg)}}")
        skin, shade = "#c9a088", "#8a6552"
        # The CSS animation owns `transform`, so placement lives on a wrapping group.
        d.add(f'<g filter="url(#{soft})"><g transform="translate({fx:.1f} {fy:.1f}) scale({s:.3f})"><g class="bob">'
              f'<g class="arm" style="animation-delay:-.42s"><rect x="-58" y="52" width="26" height="150" rx="13" fill="{shade}"/></g>'
              f'<rect x="-40" y="190" width="98" height="330" rx="40" fill="#2c3431"/>'
              f'<rect x="-50" y="48" width="104" height="170" rx="36" fill="#ece8e1"/>'
              f'<rect x="-8" y="8" width="26" height="50" rx="10" fill="{skin}"/>'
              f'<ellipse cx="4" cy="-10" rx="30" ry="36" fill="{skin}"/>'
              f'<path d="M-28-18c0-34 58-40 64-6c-12-10-40-14-64 6z" fill="#231c18"/>'
              f'<g class="arm"><rect x="36" y="52" width="26" height="160" rx="13" fill="{skin}"/></g>'
              f'</g></g></g>')


# --------------------------------------------------------------- sections ---
def ticker():
    H = 46
    d = SVG("ticker", H, "Latest news: " + " / ".join(PROFILE["ticker"]))
    size = 12
    # Buttons pinned to the right, exactly like Filmbot's header.
    labels = PROFILE["ticker_buttons"]
    red_w = 40 + MONO_B.width("→ " + labels[1], size, 0.6)
    dark_w = 40 + MONO_B.width(labels[0], size, 0.6)
    area = W - red_w - dark_w
    seg = []
    x = 0.0
    for msg in PROFILE["ticker"]:
        seg.append(f'<rect x="{x:g}" y="{H / 2 - 3:g}" width="6" height="6" fill="{PAPER}"/>')
        x += 14
        seg.append(d.text(x, H / 2 + 4.3, "LATEST NEWS", MONO_B, size - 1, PAPER, ls=0.4))
        x += MONO_B.width("LATEST NEWS", size - 1, 0.4) + 22
        seg.append(d.text(x, H / 2 + 4.3, msg, MONO, size, G300))
        x += MONO.width(msg, size) + 56
    period = x
    copies = int(area // period) + 2
    group = "".join(f'<g transform="translate({i * period:.1f} 0)">{"".join(seg)}</g>' for i in range(copies))
    d.css.append(f".mq{{animation:mq {period / 38:.1f}s linear infinite}}"
                 f"@keyframes mq{{to{{transform:translateX(-{period:.1f}px)}}}}")
    cid = d.clip_rect(0, 0, area, H)
    d.add(f'<g clip-path="url(#{cid})"><g transform="translate(18 0)"><g class="mq">{group}</g></g></g>')
    d.add(f'<rect x="{area:g}" y="0" width="{dark_w:g}" height="{H}" fill="{G900}"/>')
    d.add(d.text(area + 20, H / 2 + 4.6, labels[0], MONO_B, size, PAPER, ls=0.6))
    button(d, area + dark_w, 0, labels[1], size=size, h=H)
    d.save()


def hero():
    H = 600
    c = PROFILE["hero"]
    d = SVG("hero", H, f"{PROFILE['handle']} — {c['kicker'].lower()} {' '.join(c['title']).lower()}. {c['sub']}")
    paper(d)
    # Three staggered rounded film frames reveal one continuous tracking shot.
    frames = [(28, 28, 118, 404), (156, 112, 118, 404), (284, 196, 118, 376)]
    cid = d.uid("f")
    d.defs.append(f'<clipPath id="{cid}">' + "".join(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="30"/>' for x, y, w, h in frames) + "</clipPath>")
    d.add(f'<g clip-path="url(#{cid})" class="fade">')
    motion_scene(d, 28, 28, 374, 544)
    grain(d, 28, 28, 374, 544)
    d.add("</g>")

    cx, maxw = 695, 520
    size = fit(BOLD, c["title"], maxw, 160, -0.01)
    top = 138
    film_icon(d, cx, top)
    ky = top + 76
    d.add(f'<g class="up" style="animation-delay:.05s">{d.text(cx, ky, c["kicker"], MED, 34, G900, "middle", 0.4)}</g>')
    last = headline(d, c["title"], cx, ky + 18 + size * 0.72, size, G900, "middle", delay=0.15)
    d.add(d.text(cx, last + 60, c["sub"], MED, 22, G700, "middle", cls="up", style="animation-delay:.6s"))
    d.add(d.text(cx, 556, PROFILE["handle"], BOLD, 26, G900, "middle", 1.5, cls="fade", style="animation-delay:.8s"))
    d.save()


def about():
    H = 360
    c = PROFILE["about"]
    d = SVG("about", H, f"{c['lead']} {c['rest']}")
    size, x, maxw = 42, 56, 860
    # Lead sentence in white, the rest in grey — flowing on as one paragraph.
    words = [(w, PAPER) for w in c["lead"].split()] + [(w, G500) for w in c["rest"].split()]
    lines, cur = [], []
    for w in words:
        trial = " ".join(t for t, _ in cur + [w])
        if cur and MED.width(trial, size) > maxw:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    lines.append(cur)
    y = 104
    for i, line in enumerate(lines):
        runs, cx = [], x
        for j, (word, col) in enumerate(line):
            piece = (" " if j else "") + word
            runs.append(d.text(cx, y + i * size * 1.18, piece, MED, size, col))
            cx += MED.width(piece, size)
        d.add(f'<g class="up" style="animation-delay:{0.1 + i * 0.08:.2f}s">{"".join(runs)}</g>')
    d.add(f'<line x1="{x}" x2="{W - x}" y1="{H - 96}" y2="{H - 96}" stroke="{G800}"/>')
    d.add(d.text(x, H - 52, c["caption"], MONO_B, 12, G400, ls=0.6, cls="fade", style="animation-delay:.6s"))
    tx = W - x
    for tag in reversed(c["tags"]):
        tw = MONO_B.width(tag, 12, 0.6) + 36
        tx -= tw
        d.add(f'<g class="fade" style="animation-delay:.7s"><rect x="{tx:g}" y="{H - 76}" width="{tw:g}" height="38" '
              f'rx="19" fill="none" stroke="{G700}"/>'
              + d.text(tx + tw / 2, H - 52, tag, MONO_B, 12, PAPER, "middle", 0.6) + "</g>")
        tx -= 10
    d.save()


def skills():
    H = 620
    c = PROFILE["skills"]
    cols = c["columns"]
    d = SVG("skills", H, "Skills — " + "; ".join(f"{k}: {', '.join(v)}" for k, v in cols.items()))
    paper(d)
    x = 56
    bracket(d, x, 88, c["kicker"], G700)
    size = fit(BOLD, c["title"], 400, 124, -0.01)
    last = headline(d, c["title"], x - 4, 118 + size * 0.72, size, G900)
    paragraph(d, c["body"], x, last + 62, 20, G700, 380)

    colx = [520, 752]
    for ci, (head, items) in enumerate(cols.items()):
        cx0 = colx[ci]
        d.add(d.text(cx0, 88, head, MONO_B, 12, G700, ls=0.6))
        for i, item in enumerate(items):
            ry = 112 + i * 52
            delay = 0.2 + (ci * 3 + i) * 0.05
            d.add(f'<g class="up" style="animation-delay:{delay:.2f}s">'
                  f'<line x1="{cx0}" x2="{cx0 + 212}" y1="{ry}" y2="{ry}" stroke="{G300}"/>'
                  f'<rect x="{cx0}" y="{ry + 22}" width="7" height="7" fill="{RED if i == 0 else G900}"/>'
                  + d.text(cx0 + 20, ry + 31, item, MONO_B, 14, G900, ls=0.3) + "</g>")
        end = 112 + len(items) * 52
        d.add(f'<line x1="{cx0}" x2="{cx0 + 212}" y1="{end}" y2="{end}" stroke="{G300}"/>')
    d.save()


def odometer(d, right, base, value, size, fill, delay):
    """Rolling digit reels that settle on the value — Filmbot's stat counter."""
    digits = str(value)
    dw = max(BOLD.width(str(i), size) for i in range(10))
    pw = BOLD.width("%", size)
    x0 = right - pw - dw * len(digits) - 4
    pitch = size * 1.02
    cid = d.clip_rect(x0 - 2, base - size * 0.8, dw * len(digits) + 4, size * 0.92)
    reels = []
    for i, ch in enumerate(digits):
        stop = (10 + i * 10 + int(ch)) * pitch
        name = d.uid("odo")
        d.css.append(f".{name}{{animation:{name} {2.2 + i * 0.3:.1f}s cubic-bezier(.2,.8,.2,1) {delay:.2f}s both}}"
                     f"@keyframes {name}{{from{{transform:translateY(0)}}to{{transform:translateY(-{stop:.1f}px)}}}}")
        count = 11 + i * 10 + int(ch)
        col = "".join(d.text(x0 + dw * (i + 0.5), base + k * pitch, str(k % 10), BOLD, size, fill, "middle")
                      for k in range(count))
        reels.append(f'<g class="{name}">{col}</g>')
    d.add(f'<g clip-path="url(#{cid})">{"".join(reels)}</g>')
    d.add(d.text(right, base, "%", BOLD, size, fill, "end"))


def stats():
    H = 440
    c = PROFILE["stats"]
    d = SVG("stats", H, "Where the hours go: " + ", ".join(f"{k.lower()} {v}%" for k, v in c["bars"]))
    x = 56
    bracket(d, x, 88, c["kicker"], G400)
    size = fit(BOLD, c["title"], 400, 112, -0.01)
    last = headline(d, c["title"], x - 3, 118 + size * 0.72, size, PAPER)
    paragraph(d, c["body"], x, last + 60, 20, G400, 360)
    d.add(d.text(x, H - 48, c["footnote"], MONO, 11, G500, cls="fade", style="animation-delay:1s"))

    d.css.append(".grow{transform-box:fill-box;transform-origin:0 50%;"
                 "animation:grow 2.2s cubic-bezier(.2,.8,.2,1) both}@keyframes grow{from{transform:scaleX(0)}}")
    left, right = 520, W - 56
    for i, (label, value) in enumerate(c["bars"]):
        y = 96 + i * 100
        delay = 0.3 + i * 0.25
        d.add(d.text(left, y + 8, label, MONO_B, 13, G300, ls=0.6))
        odometer(d, right, y + 48, value, 64, PAPER if i else RED, delay)
        track = right - left - 150
        d.add(f'<rect x="{left}" y="{y + 30}" width="{track}" height="12" fill="{G800}"/>')
        d.add(f'<rect x="{left}" y="{y + 30}" width="{track * value / 100:.1f}" height="12" '
              f'fill="{RED if i == 0 else PAPER}" class="grow" style="animation-delay:{delay:.2f}s"/>')
    d.save()


def cinema_art(d, x, y, w, h):
    """Dark auditorium: flickering screen, projector beam, dust and silhouettes."""
    d.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#0f0f10"/>')
    sx, sy, sw, sh = x + w * 0.12, y + h * 0.16, w * 0.76, h * 0.4
    spill = d.uid("spill")
    d.defs.append(f'<radialGradient id="{spill}" cx=".5" cy="0" r="1">'
                  f'<stop offset="0" stop-color="#cfe0da" stop-opacity=".28"/>'
                  f'<stop offset=".7" stop-color="#cfe0da" stop-opacity="0"/></radialGradient>')
    d.add(f'<rect x="{x}" y="{sy + sh}" width="{w}" height="{h}" fill="url(#{spill})"/>')
    scid = d.clip_rect(sx, sy, sw, sh)
    d.css.append(".flick{animation:flick 3s steps(1) infinite}"
                 "@keyframes flick{0%{opacity:1}7%{opacity:.86}9%{opacity:1}43%{opacity:.92}45%{opacity:1}}")
    d.add(f'<g clip-path="url(#{scid})" class="flick">')
    motion_scene(d, sx, sy, sw, sh, seed=11, speed=7)
    d.add("</g>")
    d.add(f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="none" stroke="#fff6e0" stroke-opacity=".25"/>')
    rng = random.Random(4)
    d.css.append(".dust{animation:dust 6s linear infinite}@keyframes dust{from{transform:translateY(0);opacity:0}"
                 "20%{opacity:.9}to{transform:translateY(-120px);opacity:0}}")
    for _ in range(26):
        px, py = x + rng.uniform(w * 0.3, w * 0.7), y + rng.uniform(h * 0.55, h * 0.95)
        d.add(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{rng.uniform(.6, 1.6):.1f}" fill="#fff6e0" class="dust" '
              f'style="animation-delay:-{rng.uniform(0, 6):.1f}s"/>')
    for row, (ry, r, n, col) in enumerate([(0.78, 22, 7, "#1a1a1b"), (0.9, 28, 6, "#070707")]):
        seats = []
        for k in range(n):
            hx = x + w * (k + 0.5 + (0.5 if row == 0 else 0) - 0.25) / n
            seats.append(f'<circle cx="{hx:.1f}" cy="{y + h * ry:.1f}" r="{r * 0.62:.1f}"/>'
                         f'<rect x="{hx - r * 1.2:.1f}" y="{y + h * ry + r * 0.4:.1f}" width="{r * 2.4:.1f}" height="{h}" rx="{r}"/>')
        d.add(f'<g fill="{col}">{"".join(seats)}</g>')


def leader_art(d, x, y, w, h):
    """Academy countdown leader: sweeping wedge, crosshairs, 3-2-1."""
    d.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#5f5b56"/>')
    cx, cy, r = x + w / 2, y + h / 2, min(w, h) * 0.34
    circ = 2 * 3.14159265 * (r * 1.2)
    d.css.append(f".sweep{{animation:sweep 1s linear infinite}}"
                 f"@keyframes sweep{{from{{stroke-dashoffset:{circ:.1f}}}to{{stroke-dashoffset:0}}}}")
    d.add(f'<circle cx="{cx}" cy="{cy}" r="{r * 1.2:.1f}" fill="none" stroke="#3b3834" stroke-width="{r * 2.4:.1f}" '
          f'stroke-dasharray="{circ:.1f}" class="sweep" transform="rotate(-90 {cx} {cy})" clip-path="url(#{d.clip_rect(x, y, w, h)})"/>')
    ring = "#e8e2d6"
    d.add(f'<g fill="none" stroke="{ring}" stroke-width="3" opacity=".85">'
          f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}"/><circle cx="{cx}" cy="{cy}" r="{r * 0.82:.1f}"/>'
          f'<line x1="{x}" x2="{x + w}" y1="{cy}" y2="{cy}"/><line x1="{cx}" x2="{cx}" y1="{y}" y2="{y + h}"/></g>')
    for i, num in enumerate("321"):
        name = d.uid("n")
        d.css.append(f".{name}{{animation:{name} 3s steps(1) infinite}}"
                     f"@keyframes {name}{{0%{{opacity:0}}{i * 33.33:.2f}%{{opacity:1}}{(i + 1) * 33.33:.2f}%{{opacity:0}}}}")
        d.add(d.text(cx, cy + r * 0.52, num, BOLD, r * 1.45, ring, "middle", cls=name))
    d.css.append(".scratch{animation:scratch .9s steps(1) infinite}"
                 "@keyframes scratch{0%{transform:translateX(0)}30%{transform:translateX(140px)}"
                 "60%{transform:translateX(-90px)}80%{transform:translateX(60px)}}")
    d.add(f'<g class="scratch" opacity=".35"><line x1="{x + w * 0.3}" x2="{x + w * 0.31}" y1="{y}" y2="{y + h}" '
          f'stroke="#fff" stroke-width="1.2"/></g>')


def project(p):
    H = 500
    d = SVG(p["file"], H, f"{p['label']} {p['num']}: {' '.join(p['title']).title()} — {p['body']}")
    paper(d)
    ax, ay, aw, ah = 28, 28, 452, H - 56
    aid = d.clip_rect(ax, ay, aw, ah, 10)
    d.add(f'<g clip-path="url(#{aid})">')
    (cinema_art if p["art"] == "cinema" else leader_art)(d, ax, ay, aw, ah)
    grain(d, ax, ay, aw, ah, opacity=0.18)
    d.add("</g>")
    bracket(d, ax + 22, ay + ah - 24, p["caption"])

    x, right = 530, W - 56
    d.add(d.text(x, 80, p["label"], MED, 22, G700, cls="fade"))
    d.add(d.text(right, 80, p["num"], MONO_B, 14, G700, "end", cls="fade"))
    d.add(f'<line x1="{x}" x2="{right}" y1="{98}" y2="{98}" stroke="{G300}"/>')
    size = fit(BOLD, p["title"], right - x, 96, -0.01)
    last = headline(d, p["title"], x - 3, 126 + size * 0.72, size, G900)
    end = paragraph(d, p["body"], x, last + 52, 20, G700, right - x)
    d.add(f'<g class="up" style="animation-delay:.8s">')
    button(d, x, end + 32, p["cta"])
    d.add("</g>")
    d.save()


def marquee_art(d, x, y, w, h, lines):
    """Cinema marquee with chasing bulbs."""
    d.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#141112"/>')
    glow = d.uid("glow")
    d.defs.append(f'<radialGradient id="{glow}"><stop offset="0" stop-color="{RED}" stop-opacity=".35"/>'
                  f'<stop offset="1" stop-color="{RED}" stop-opacity="0"/></radialGradient>')
    d.add(f'<ellipse cx="{x + w / 2}" cy="{y + h / 2}" rx="{w * 0.7}" ry="{h * 0.6}" fill="url(#{glow})"/>')
    mx, my, mw, mh = x + 34, y + 58, w - 68, h - 150
    d.add(f'<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="8" fill="{RED}"/>')
    bx, by, bw, bh = mx + 30, my + 30, mw - 60, mh - 60
    d.add(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="3" fill="{PAPER}"/>')
    d.add(d.text(bx + bw / 2, by + 42, lines[0], MONO_B, 13, G900, "middle", 1.4))
    size = fit(BOLD, lines[1:], bw - 50, 88)
    headline(d, lines[1:], bx + bw / 2, by + 62 + size * 0.72, size, G900, "middle", delay=0.3, lh=0.9)
    d.css.append(".bulb{animation:bulb .9s steps(1) infinite}@keyframes bulb{50%{fill:#5a3b22}}")
    pts, step = [], 22
    per = [(mx + 15 + i * step, my + 15) for i in range(int((mw - 30) / step) + 1)]
    side = [(mx + mw - 15, my + 15 + i * step) for i in range(1, int((mh - 30) / step) + 1)]
    pts = per + side + [(px, my + mh - 15) for px, _ in reversed(per[:-1])] + \
        [(mx + 15, py) for _, py in reversed(side[:-1])]
    bulbs = "".join(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="#ffd9a0" class="bulb" '
                    f'style="animation-delay:-{(k % 3) * 0.3:.1f}s"/>' for k, (px, py) in enumerate(pts))
    d.add(f'<g>{bulbs}</g>')
    d.add(f'<rect x="{x + w / 2 - 70}" y="{my + mh}" width="14" height="{h}" fill="#241e1f"/>'
          f'<rect x="{x + w / 2 + 56}" y="{my + mh}" width="14" height="{h}" fill="#241e1f"/>')


def contact():
    H = 480
    c = PROFILE["contact"]
    d = SVG("contact", H, f"{' '.join(c['title']).title()} — {c['body']}")
    x = 56
    size = fit(BOLD, c["title"], 430, 120, -0.01)
    last = headline(d, c["title"], x - 4, 70 + size * 0.72, size, PAPER)
    d.add(d.text(x, last + 56, c["kicker"], MONO_B, 13, RED, ls=0.8, cls="fade", style="animation-delay:.4s"))
    end = paragraph(d, c["body"], x, last + 100, 20, G400, 420)
    d.add('<g class="up" style="animation-delay:.8s">')
    button(d, x, end + 38, c["cta"])
    d.add("</g>")
    ax, ay, aw, ah = 540, 28, W - 540 - 28, H - 56
    aid = d.clip_rect(ax, ay, aw, ah, 10)
    d.add(f'<g clip-path="url(#{aid})">')
    marquee_art(d, ax, ay, aw, ah, c["sign"])
    grain(d, ax, ay, aw, ah, opacity=0.12)
    d.add("</g>")
    bracket(d, ax + 22, ay + ah - 24, c["caption"])
    d.save()


def footer():
    H = 300
    c = PROFILE["footer"]
    d = SVG("footer", H, f"{PROFILE['handle']} — {c['mid'].lower()}")
    size = fit(BOLD, [PROFILE["handle"]], W - 112, 220, -0.01)
    headline(d, [PROFILE["handle"]], W / 2, 196, size, PAPER, "middle")
    y = H - 40
    d.add(f'<line x1="56" x2="{W - 56}" y1="{y - 34}" y2="{y - 34}" stroke="{G800}"/>')
    d.add(d.text(56, y, c["left"], MONO_B, 12, G400, ls=0.6))
    d.css.append(".glow{animation:glow 2.4s ease-in-out infinite}@keyframes glow{50%{opacity:.45}}")
    mw = MONO_B.width(c["mid"], 12, 0.6)
    d.add(f'<g class="glow"><rect x="{W / 2 - mw / 2 - 16}" y="{y - 9}" width="7" height="7" fill="{RED}"/>'
          + d.text(W / 2 + 6, y, c["mid"], MONO_B, 12, RED, "middle", 0.6) + "</g>")
    d.add(d.text(W - 56, y, c["right"], MONO_B, 12, G400, "end", 0.6))
    d.save()


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    print(f"Writing SVGs to {OUT}")
    ticker()
    hero()
    about()
    skills()
    stats()
    for p in PROFILE["projects"]:
        project(p)
    contact()
    footer()
