#!/usr/bin/env python3
"""Builds the cave-themed SVG sections used around the banner in the profile README.

Edit PROFILE below, then run:

    pip install fonttools
    python _src/build.py

Every SVG in ../assets is regenerated (the banner, assets/batcave.gif, is left
alone). Text is converted to vector outlines (Barlow Condensed + JetBrains Mono,
both OFL — see _src/fonts), so it looks the same on every device without
loading any fonts.
"""
import html
import math
import random
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

SRC = Path(__file__).resolve().parent
OUT = SRC.parent / "assets"

# ---------------------------------------------------------------- content ---
PROFILE = {
    "name": "SATURDAYS",
    "handle": "NEBXD1",
    # Cycles above the name in the identity panel.
    "roles": ["FULL STACK DEVELOPER", "DESIGNER", "AI WORKFLOW BUILDER"],
    "tagline": "EXPLORING AI, DISTRIBUTED SYSTEMS & SCALABLE ARCHITECTURES",
    # (label, line) rows of the mission briefing; the mission itself closes it.
    "briefing": [
        ("PROFILE", "Full stack developer passionate about building impactful products."),
        ("BUILDING", "Products for the next generation of the internet."),
        ("LEARNING", "Constantly learning and experimenting with new technologies."),
    ],
    "mission": "EMPOWER PEOPLE THROUGH TECHNOLOGY AND INNOVATION",
    # (name, detail, monitor art: "code" | "design" | "ai")
    "disciplines": [
        ("FULL STACK", "HTML · CSS · JAVASCRIPT", "code"),
        ("DESIGN", "UI & VISUAL DESIGN", "design"),
        ("AI WORKFLOWS", "AI-POWERED AUTOMATION", "ai"),
    ],
    "ticker": [
        "SATURDAYS — FULL STACK DEVELOPER · DESIGNER · AI WORKFLOWS",
        "EXPLORING AI, DISTRIBUTED SYSTEMS & SCALABLE ARCHITECTURES",
        "MISSION: EMPOWER PEOPLE THROUGH TECHNOLOGY",
        "STATUS: ONLINE",
    ],
    "ticker_buttons": ["REPOSITORIES", "FOLLOW"],
    "footer": {
        "left": "© 2026 SATURDAYS",
        "mid": "END OF TRANSMISSION",
        "right": "GITHUB.COM/NEBXD1",
    },
}

# ------------------------------------------------------------------ style ---
# Pulled from the banner: cave black, monitor blue, waterfall ice, lamp amber.
W = 1000
BG, PANEL, PANEL2, LINE = "#05080E", "#08101B", "#0D1726", "#1B2A3D"
BLUE, ICE, AMBER = "#4DB2FF", "#A9DBFF", "#F2B45A"
TEXT, MUTED, DIM = "#E8EEF6", "#7F93AB", "#4A5B70"

BASE_CSS = """
.rise{animation:rise 1.2s cubic-bezier(.16,1,.3,1) both}
@keyframes rise{from{transform:translateY(200px)}}
.fade{animation:fade 1s ease both}
@keyframes fade{from{opacity:0}}
.up{animation:up 1s cubic-bezier(.16,1,.3,1) both}
@keyframes up{from{opacity:0;transform:translateY(14px)}}
.blink{animation:blink 1.1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
"""

BAT = ("M0 -4L3 -9L4 -4C10 -6 18 -10 30 -8C26 -4 25 0 26 4C22 1 18 2 15 5C13 2 9 2 6 6"
       "C4 4 2 5 0 8C-2 5 -4 4 -6 6C-9 2 -13 2 -15 5C-18 2 -22 1 -26 4C-25 0 -26 -4 -30 -8"
       "C-18 -10 -10 -6 -4 -4L-3 -9Z")


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
    def __init__(self, name, h, title, corners="none"):
        self.name, self.h, self.title, self.corners = name, h, title, corners
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

    def glow_filter(self, dev=8):
        fid = self.uid("glow")
        self.defs.append(f'<filter id="{fid}" x="-30%" y="-60%" width="160%" height="220%">'
                         f'<feGaussianBlur stdDeviation="{dev}"/></filter>')
        return fid

    def card_path(self):
        # Ticker rounds the top, footer the bottom; together with the square
        # banner in between they read as one screen.
        h, r = self.h, 14
        if self.corners == "top":
            return f"M0 {h}V{r}A{r} {r} 0 0 1 {r} 0H{W - r}A{r} {r} 0 0 1 {W} {r}V{h}Z"
        if self.corners == "bottom":
            return f"M0 0H{W}V{h - r}A{r} {r} 0 0 1 {W - r} {h}H{r}A{r} {r} 0 0 1 0 {h - r}Z"
        return f"M0 0H{W}V{h}H0Z"

    def render(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{self.h}" '
                f'viewBox="0 0 {W} {self.h}" role="img" aria-labelledby="t">'
                f'<title id="t">{esc(self.title)}</title>'
                f'<defs><clipPath id="card"><path d="{self.card_path()}"/></clipPath>'
                f'{"".join(self.defs)}</defs><style>{"".join(self.css)}</style>'
                f'<g clip-path="url(#card)"><rect width="{W}" height="{self.h}" fill="{BG}"/>'
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


def headline(d, lines, x, y, size, fill, anchor="start", delay=0.1, step=0.12, lh=0.86, glow=None):
    """Big condensed caps that rise into place line by line, with an optional monitor glow."""
    ls = -0.01 * size
    fid = d.glow_filter(size / 14) if glow else None
    for i, line in enumerate(lines):
        base = y + i * size * lh
        cid = d.clip_rect(0, base - size * 1.1, W, size * 1.4)
        t = d.text(x, base, line, BOLD, size, fill, anchor, ls)
        halo = (f'<g filter="url(#{fid})" opacity=".55">{d.text(x, base, line, BOLD, size, glow, anchor, ls)}</g>'
                if glow else "")
        d.add(f'<g clip-path="url(#{cid})"><g class="rise" style="animation-delay:{delay + i * step:.2f}s">'
              f'{halo}{t}</g></g>')
    return y + (len(lines) - 1) * size * lh


def bracket(d, x, y, label, fill=MUTED, size=12, anchor="start"):
    d.add(d.text(x, y, f"[ {label} ]", MONO_B, size, fill, anchor, ls=0.5))


def hud_corners(d, x, y, w, h, arm=18, color=BLUE):
    """L-shaped targeting brackets at each corner of a box."""
    pts = [(x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)]
    path = "".join(f"M{cx + sx * arm} {cy}H{cx}V{cy + sy * arm}" for cx, cy, sx, sy in pts)
    d.add(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" opacity=".8"/>')


def scanlines(d, x, y, w, h, band=True):
    """CRT scanlines plus a slow sweep of light, like the cave's monitors."""
    pid = d.uid("scan")
    d.defs.append(f'<pattern id="{pid}" width="4" height="4" patternUnits="userSpaceOnUse">'
                  f'<rect width="4" height="1" fill="#fff" opacity=".035"/></pattern>')
    d.add(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="url(#{pid})"/>')
    if band:
        gid, name = d.uid("band"), d.uid("sweep")
        d.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
                      f'<stop offset="0" stop-color="{BLUE}" stop-opacity="0"/>'
                      f'<stop offset=".5" stop-color="{BLUE}" stop-opacity=".07"/>'
                      f'<stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></linearGradient>')
        d.css.append(f".{name}{{animation:{name} 6s linear infinite}}"
                     f"@keyframes {name}{{from{{transform:translateY(-120px)}}to{{transform:translateY({h + 120:.0f}px)}}}}")
        cid = d.clip_rect(x, y, w, h)
        d.add(f'<g clip-path="url(#{cid})"><rect x="{x:g}" y="{y:g}" width="{w:g}" height="120" '
              f'fill="url(#{gid})" class="{name}"/></g>')


def grid(d, x, y, w, h, step=40):
    pid = d.uid("grid")
    d.defs.append(f'<pattern id="{pid}" width="{step}" height="{step}" patternUnits="userSpaceOnUse" '
                  f'x="{x:g}" y="{y:g}"><path d="M{step} 0H0V{step}" fill="none" stroke="{LINE}" '
                  f'stroke-width="1" opacity=".45"/></pattern>')
    d.add(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="url(#{pid})"/>')


def bat(d, cx, cy, scale, fill, glow=False, flap=False):
    wrap = ""
    if flap:
        d.css.append(".flap{transform-box:fill-box;transform-origin:50% 40%;"
                     "animation:flap .22s ease-in-out infinite alternate}"
                     "@keyframes flap{to{transform:scaleY(.35)}}")
        wrap = ' class="flap"'
    shape = f'<path d="{BAT}" fill="{fill}"/>'
    halo = ""
    if glow:
        halo = f'<g filter="url(#{d.glow_filter(4)})" opacity=".8">{shape}</g>'
    return (f'<g transform="translate({cx:g} {cy:g}) scale({scale:g})"><g{wrap}>'
            f'{halo}{shape}</g></g>')


def status_dot(d, x, y, color=BLUE):
    d.add(f'<g class="blink"><circle cx="{x}" cy="{y}" r="4" fill="{color}"/>'
          f'<circle cx="{x}" cy="{y}" r="8" fill="{color}" opacity=".25"/></g>')


# --------------------------------------------------------------- sections ---
def ticker():
    H = 46
    d = SVG("ticker", H, "System feed: " + " / ".join(PROFILE["ticker"]), corners="top")
    size = 12
    labels = PROFILE["ticker_buttons"]
    arrow = MONO_B.width("→ ", size) + 6
    blue_w = 40 + arrow + MONO_B.width(labels[1], size, 0.6)
    dark_w = 40 + MONO_B.width(labels[0], size, 0.6)
    area = W - blue_w - dark_w
    seg, x = [], 0.0
    for msg in PROFILE["ticker"]:
        seg.append(f'<rect x="{x:g}" y="{H / 2 - 3:g}" width="6" height="6" fill="{BLUE}"/>')
        x += 14
        seg.append(d.text(x, H / 2 + 4.3, "SYSTEM FEED", MONO_B, size - 1, TEXT, ls=0.4))
        x += MONO_B.width("SYSTEM FEED", size - 1, 0.4) + 22
        seg.append(d.text(x, H / 2 + 4.3, msg, MONO, size, MUTED))
        x += MONO.width(msg, size) + 56
    period = x
    copies = int(area // period) + 2
    group = "".join(f'<g transform="translate({i * period:.1f} 0)">{"".join(seg)}</g>' for i in range(copies))
    d.css.append(f".mq{{animation:mq {period / 38:.1f}s linear infinite}}"
                 f"@keyframes mq{{to{{transform:translateX(-{period:.1f}px)}}}}")
    cid = d.clip_rect(0, 0, area, H)
    d.add(f'<g clip-path="url(#{cid})"><g transform="translate(22 0)"><g class="mq">{group}</g></g></g>')
    d.add(f'<rect x="{area:g}" y="0" width="{dark_w:g}" height="{H}" fill="{PANEL2}"/>')
    d.add(d.text(area + 20, H / 2 + 4.6, labels[0], MONO_B, size, TEXT, ls=0.6))
    bx = area + dark_w
    d.add(f'<rect x="{bx:g}" y="0" width="{blue_w:g}" height="{H}" fill="{BLUE}"/>')
    d.css.append(".nudge{animation:nudge 1.6s ease-in-out infinite}@keyframes nudge{50%{transform:translateX(4px)}}")
    d.add(f'<g class="nudge">{d.text(bx + 20, H / 2 + 4.6, "→", MONO_B, size, BG)}</g>')
    d.add(d.text(bx + 20 + arrow, H / 2 + 4.6, labels[1], MONO_B, size, BG, ls=0.6))
    d.add(f'<rect y="{H - 1}" width="{W}" height="1" fill="{LINE}"/>')
    d.save()


def hero():
    """Identity readout under the banner: role, name, handle."""
    H = 420
    p = PROFILE
    roles = ", ".join(r.lower() for r in p["roles"])
    d = SVG("hero", H, f"{p['name']} — {roles}. {p['tagline'].capitalize()}.")
    px, py, pw, ph = 12, 12, W - 24, H - 24
    d.add(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="{PANEL}"/>')
    grid(d, px, py, pw, ph)
    glow = d.uid("pool")
    d.defs.append(f'<radialGradient id="{glow}" cx=".5" cy=".55" r=".55">'
                  f'<stop offset="0" stop-color="{BLUE}" stop-opacity=".16"/>'
                  f'<stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>')
    d.add(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="url(#{glow})"/>')
    scanlines(d, px, py, pw, ph)
    d.add(f'<rect x="{px + .5}" y="{py + .5}" width="{pw - 1}" height="{ph - 1}" fill="none" stroke="{LINE}"/>')
    hud_corners(d, 32, 32, W - 64, H - 64)

    bracket(d, 56, 70, "IDENTITY")
    d.add(d.text(W - 56, 70, f"USER ID // {p['handle']}", MONO_B, 12, MUTED, "end", 0.5))

    cx = W / 2
    d.add(f'<g class="fade">{bat(d, cx, 100, 1.5, BLUE, glow=True)}</g>')
    # Roles take turns sliding through a slot above the name.
    n, hold = len(p["roles"]), 3
    cycle = n * hold
    step = 100 / n
    d.css.append(f".role{{animation:role {cycle}s cubic-bezier(.16,1,.3,1) infinite both}}"
                 f"@keyframes role{{0%{{transform:translateY(34px);opacity:0}}"
                 f"{step * .15:.1f}%,{step * .85:.1f}%{{transform:translateY(0);opacity:1}}"
                 f"{step:.1f}%,100%{{transform:translateY(-34px);opacity:0}}}}")
    cid = d.clip_rect(0, 118, W, 42)
    slots = "".join(d.text(cx, 150, role, MED, 30, ICE, "middle", 4, cls="role",
                           style=f"animation-delay:{i * hold}s") for i, role in enumerate(p["roles"]))
    d.add(f'<g clip-path="url(#{cid})">{slots}</g>')
    size = fit(BOLD, [p["name"]], 820, 176, -0.01)
    base = headline(d, [p["name"]], cx, 168 + size * 0.72, size, TEXT, "middle", delay=0.15, glow=BLUE)

    sub = p["tagline"]
    sw = MONO_B.width(sub, 13, 0.8)
    d.add(d.text(cx - 8, base + 50, sub, MONO_B, 13, MUTED, "middle", 0.8, cls="up", style="animation-delay:.6s"))
    d.add(f'<rect x="{cx - 8 + sw / 2 + 8:.1f}" y="{base + 38}" width="9" height="15" fill="{AMBER}" class="blink"/>')

    status_dot(d, 60, H - 57)
    d.add(d.text(76, H - 52, "STATUS: ONLINE", MONO_B, 12, TEXT, ls=0.5))
    d.add(d.text(W - 56, H - 52, "ACCESS: PUBLIC", MONO_B, 12, MUTED, "end", 0.5))
    d.save()


def art_code(d, x, y, w, h):
    size = 52
    sy = y + h / 2 + size * 0.36
    return (f'<g filter="url(#{d.glow_filter(9)})">{d.text(x + w / 2, sy, "</>", MONO_B, size, BLUE, "middle")}</g>'
            + d.text(x + w / 2, sy, "</>", MONO_B, size, ICE, "middle"))


def art_design(d, x, y, w, h):
    """A pen-tool bezier that draws itself, with anchors and handles."""
    a0, c0 = (x + 30, y + h * 0.72), (x + w * 0.34, y + h * 0.08)
    c1, a1 = (x + w * 0.62, y + h * 0.98), (x + w - 30, y + h * 0.3)
    curve = f"M{a0[0]:.0f} {a0[1]:.0f}C{c0[0]:.0f} {c0[1]:.0f} {c1[0]:.0f} {c1[1]:.0f} {a1[0]:.0f} {a1[1]:.0f}"
    d.css.append(".pen{stroke-dasharray:420;animation:pen 5s cubic-bezier(.6,0,.2,1) infinite}"
                 "@keyframes pen{0%{stroke-dashoffset:420}45%,85%{stroke-dashoffset:0}100%{stroke-dashoffset:-420}}")
    handles = "".join(f'<line x1="{a[0]:.0f}" y1="{a[1]:.0f}" x2="{c[0]:.0f}" y2="{c[1]:.0f}"/>'
                      for a, c in ((a0, c0), (a1, c1)))
    knobs = "".join(f'<circle cx="{c[0]:.0f}" cy="{c[1]:.0f}" r="4.5"/>' for c in (c0, c1))
    anchors = "".join(f'<rect x="{a[0] - 5:.0f}" y="{a[1] - 5:.0f}" width="10" height="10"/>' for a in (a0, a1))
    return (f'<g stroke="{MUTED}" stroke-width="1.2" opacity=".8">{handles}</g>'
            f'<path d="{curve}" fill="none" stroke="{BLUE}" stroke-width="7" opacity=".6" class="pen" '
            f'filter="url(#{d.glow_filter(5)})"/>'
            f'<path d="{curve}" fill="none" stroke="{ICE}" stroke-width="3" class="pen"/>'
            f'<g fill="{PANEL}" stroke="{ICE}" stroke-width="1.5">{knobs}{anchors}</g>')


def art_ai(d, x, y, w, h):
    """A small workflow graph with data pulsing along its edges."""
    pos = [(.16, .3), (.16, .72), (.5, .2), (.5, .5), (.5, .8), (.84, .5)]
    pts = [(x + w * px, y + h * py) for px, py in pos]
    edges = [(0, 2), (0, 3), (1, 3), (1, 4), (2, 5), (3, 5), (4, 5)]
    d.css.append(".flow{stroke-dasharray:3 9;animation:flow 1.2s linear infinite}"
                 "@keyframes flow{to{stroke-dashoffset:-24}}"
                 ".pulse{transform-box:fill-box;transform-origin:center;animation:pulse 1.6s ease-in-out infinite}"
                 "@keyframes pulse{50%{transform:scale(1.35)}}")
    lines = "".join(f'<line x1="{pts[a][0]:.0f}" y1="{pts[a][1]:.0f}" x2="{pts[b][0]:.0f}" y2="{pts[b][1]:.0f}"/>'
                    for a, b in edges)
    nodes = "".join(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="7"/>' for px, py in pts[:-1])
    ox, oy = pts[-1]
    return (f'<g stroke="{BLUE}" stroke-width="1.5" opacity=".35">{lines}</g>'
            f'<g stroke="{ICE}" stroke-width="2.5" class="flow">{lines}</g>'
            f'<g fill="{PANEL}" stroke="{ICE}" stroke-width="2">{nodes}</g>'
            f'<circle cx="{ox:.0f}" cy="{oy:.0f}" r="14" fill="{AMBER}" opacity=".25" class="pulse"/>'
            f'<circle cx="{ox:.0f}" cy="{oy:.0f}" r="8" fill="{AMBER}"/>')


ARTS = {"code": art_code, "design": art_design, "ai": art_ai}


def monitor(d, x, y, w, h, art, seed, delay):
    """One screen of the cave's monitor wall: scrolling code, glowing artwork, reflection."""
    rng = random.Random(seed)
    d.add(f'<ellipse cx="{x + w / 2}" cy="{y + h + 26}" rx="{w * 0.45}" ry="10" fill="{BLUE}" '
          f'opacity=".18" filter="url(#{d.glow_filter(10)})"/>')
    d.add(f'<rect x="{x - 7}" y="{y - 7}" width="{w + 14}" height="{h + 14}" rx="6" fill="#070B12" stroke="{LINE}"/>')
    sg = d.uid("scr")
    d.defs.append(f'<linearGradient id="{sg}" x1="0" y1="0" x2="1" y2="1">'
                  f'<stop offset="0" stop-color="#0E3057"/><stop offset="1" stop-color="#061423"/></linearGradient>')
    cid = d.clip_rect(x, y, w, h, 2)
    rows_h = 13
    rows = math.ceil(h / rows_h) + 1
    period = rows * rows_h
    bars = []
    for r in range(rows):
        indent = rng.choice([0, 0, 14, 14, 28, 42])
        cx = x + 14 + indent
        for _ in range(rng.randint(1, 3)):
            bw = rng.uniform(14, w * 0.32)
            if cx + bw > x + w - 14:
                break
            col = rng.choice([BLUE, BLUE, ICE, MUTED, AMBER if rng.random() < .15 else BLUE])
            for off in (0, period):
                bars.append(f'<rect x="{cx:.1f}" y="{y + 10 + r * rows_h + off:.1f}" width="{bw:.1f}" height="5" '
                            f'rx="2.5" fill="{col}" opacity="{rng.uniform(.3, .65):.2f}"/>')
            cx += bw + 7
    name = d.uid("code")
    d.css.append(f".{name}{{animation:{name} {8 + seed % 3}s linear infinite}}"
                 f"@keyframes {name}{{to{{transform:translateY(-{period}px)}}}}")
    d.add(f'<g clip-path="url(#{cid})" class="fade" style="animation-delay:{delay:.2f}s">'
          f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{sg})"/>'
          f'<g class="{name}">{"".join(bars)}</g>'
          f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{BG}" opacity=".45"/></g>')
    d.add(f'<g class="up" style="animation-delay:{delay + .2:.2f}s">{ARTS[art](d, x, y, w, h)}</g>')
    scanlines(d, x, y, w, h, band=False)


def radar(d, cx, cy, r):
    """Sweeping radar scope with blinking contacts."""
    d.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{PANEL}"/>')
    d.add(f'<g fill="none" stroke="{BLUE}" opacity=".3">'
          + "".join(f'<circle cx="{cx}" cy="{cy}" r="{r * k:.1f}"/>' for k in (1, .66, .33))
          + f'<line x1="{cx - r}" x2="{cx + r}" y1="{cy}" y2="{cy}"/>'
            f'<line x1="{cx}" x2="{cx}" y1="{cy - r}" y2="{cy + r}"/></g>')
    wedges = []
    for i in range(14):
        a0, a1 = math.radians(-i * 4), math.radians(-(i + 1) * 4)
        wedges.append(f'<path d="M{cx} {cy}L{cx + r * math.cos(a0):.1f} {cy + r * math.sin(a0):.1f}'
                      f'A{r} {r} 0 0 0 {cx + r * math.cos(a1):.1f} {cy + r * math.sin(a1):.1f}Z" '
                      f'opacity="{0.4 * (1 - i / 14):.2f}"/>')
    d.css.append(f".sweep{{transform-origin:{cx}px {cy}px;animation:sweep 4s linear infinite}}"
                 f"@keyframes sweep{{to{{transform:rotate(360deg)}}}}")
    d.add(f'<g class="sweep" fill="{BLUE}">{"".join(wedges)}'
          f'<line x1="{cx}" y1="{cy}" x2="{cx + r}" y2="{cy}" stroke="{ICE}" stroke-width="1.5"/></g>')
    for i, (bx, by) in enumerate([(.45, -.3), (-.5, .35), (.2, .6)]):
        d.add(f'<circle cx="{cx + r * bx:.1f}" cy="{cy + r * by:.1f}" r="3.5" fill="{AMBER if i == 0 else ICE}" '
              f'class="blink" style="animation-delay:{i * .35:.2f}s"/>')
    d.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{LINE}" stroke-width="2"/>')


def briefing():
    """Dossier of who I am and what I'm after, beside a radar scope."""
    p = PROFILE
    rows = p["briefing"]
    x0, x1 = 440, W - 56
    size, lh = 25, 32
    wrapped = [wrap(MED, line, size, x1 - x0) for _, line in rows]
    msize = fit(BOLD, ["TECHNOLOGY AND INNOVATION"], x1 - x0, 44)
    mission = wrap(BOLD, p["mission"], msize, x1 - x0)
    H = 70 + sum(56 + len(ls) * lh for ls in wrapped) + 60 + len(mission) * msize * 0.95 + 56
    H = max(H, 540)
    d = SVG("briefing", round(H), "Mission briefing: " + " ".join(l for _, l in rows)
            + f" Mission: {p['mission'].capitalize()}.")
    grid(d, 0, 0, W, H)
    d.add(f'<rect x="12" y="0" width="{W - 24}" height="{H}" fill="{PANEL}" opacity=".55"/>')

    x = 56
    bracket(d, x, 64, "BRIEFING")
    headline(d, ["MISSION", "BRIEFING"], x - 4, 150, 84, TEXT, glow=BLUE)
    radar(d, 196, 360, 108)
    d.add(d.text(x, H - 52, f"FILE // {p['name']}", MONO_B, 12, MUTED, ls=0.5))
    d.add(d.text(x, H - 32, "CLEARANCE // PUBLIC", MONO_B, 12, DIM, ls=0.5))

    y = 64
    for i, ((label, _), lines) in enumerate(zip(rows, wrapped)):
        delay = 0.3 + i * 0.15
        parts = [f'<line x1="{x0}" x2="{x1}" y1="{y - 18}" y2="{y - 18}" stroke="{LINE}"/>',
                 d.text(x0, y + 8, f"{i + 1:02d} // {label}", MONO_B, 12, BLUE, ls=0.6)]
        for j, line in enumerate(lines):
            parts.append(d.text(x0, y + 44 + j * lh, line, MED, size, TEXT))
        d.add(f'<g class="up" style="animation-delay:{delay:.2f}s">{"".join(parts)}</g>')
        y += 56 + len(lines) * lh + 8

    y += 10
    parts = [f'<line x1="{x0}" x2="{x1}" y1="{y - 18}" y2="{y - 18}" stroke="{AMBER}" opacity=".6"/>',
             d.text(x0, y + 8, f"{len(rows) + 1:02d} // MISSION", MONO_B, 12, AMBER, ls=0.6)]
    d.add(f'<g class="up" style="animation-delay:{0.3 + len(rows) * 0.15:.2f}s">{"".join(parts)}</g>')
    headline(d, mission, x0 - 2, y + 22 + msize * 0.72, msize, ICE,
             delay=0.4 + len(rows) * 0.15, lh=0.95, glow=BLUE)
    d.save()


def skills():
    H = 510
    items = PROFILE["disciplines"]
    d = SVG("skills", H, "What I do: " + ", ".join(f"{n.lower()} ({what.lower()})" for n, what, _ in items))
    grid(d, 0, 0, W, H)
    x = 56
    bracket(d, x, 64, "CAPABILITIES")
    headline(d, ["WHAT I DO"], x - 4, 150, 96, TEXT, delay=0.1, glow=BLUE)
    online = f"{len(items):02d} SYSTEMS ONLINE"
    status_dot(d, W - 56 - MONO_B.width(online, 12, 0.5) - 16, 139)
    d.add(d.text(W - 56, 144, online, MONO_B, 12, MUTED, "end", 0.5))

    gap = 28
    mw = (W - 2 * x - gap * (len(items) - 1)) / len(items)
    my, mh = 200, 160
    nsize = fit(BOLD, [n for n, _, _ in items], mw, 48)
    for i, (name, what, art) in enumerate(items):
        mx = x + i * (mw + gap)
        monitor(d, mx, my, mw, mh, art, seed=i + 3, delay=0.2 + i * 0.15)
        ly = my + mh + 26
        d.add(f'<g class="up" style="animation-delay:{0.4 + i * 0.15:.2f}s">'
              f'<line x1="{mx - 7}" x2="{mx + mw + 7}" y1="{ly}" y2="{ly}" stroke="{LINE}"/>'
              + d.text(mx - 6, ly + 26, f"{i + 1:02d} / {what}", MONO_B, 12, MUTED, ls=0.5)
              + d.text(mx - 8, ly + 76, name, BOLD, nsize, TEXT, ls=-0.4)
              + "</g>")
    d.save()


def footer():
    H = 170
    c = PROFILE["footer"]
    d = SVG("footer", H, f"{PROFILE['name']} — {c['mid'].lower()}", corners="bottom")
    d.add(f'<rect width="{W}" height="1" fill="{LINE}"/>')
    # Stalactites along the top edge.
    rng = random.Random(9)
    pts, x = ["0,0"], 0.0
    while x < W:
        w = rng.uniform(18, 60)
        pts.append(f"{x + w / 2:.0f},{rng.uniform(8, 46):.0f}")
        x += w
        pts.append(f"{min(x, W):.0f},{rng.uniform(0, 6):.0f}")
    pts.append(f"{W},0")
    d.add(f'<polygon points="{" ".join(pts)}" fill="{PANEL2}"/>')
    # A bat crossing the screen.
    d.css.append(".fly{animation:fly 9s linear infinite}"
                 "@keyframes fly{from{transform:translate(-80px,78px)}25%{transform:translate(240px,58px)}"
                 "50%{transform:translate(520px,84px)}75%{transform:translate(800px,62px)}"
                 "to{transform:translate(1080px,76px)}}")
    d.add(f'<g class="fly">{bat(d, 0, 0, 1.3, BLUE, glow=True, flap=True)}</g>')
    y = H - 34
    d.add(f'<line x1="56" x2="{W - 56}" y1="{y - 30}" y2="{y - 30}" stroke="{LINE}"/>')
    d.add(d.text(56, y, c["left"], MONO_B, 12, MUTED, ls=0.6))
    mw = MONO_B.width(c["mid"], 12, 0.6)
    d.add(f'<rect x="{W / 2 - mw / 2 - 16}" y="{y - 9}" width="7" height="7" fill="{AMBER}" class="blink"/>'
          + d.text(W / 2 + 6, y, c["mid"], MONO_B, 12, AMBER, "middle", 0.6))
    d.add(d.text(W - 56, y, c["right"], MONO_B, 12, MUTED, "end", 0.6))
    d.save()


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    print(f"Writing SVGs to {OUT}")
    ticker()
    hero()
    briefing()
    skills()
    footer()
