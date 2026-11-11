# -*- coding: utf-8 -*-
"""Drawing library of the WebConform method figures (SVG, converted to PDF with cairosvg).

Visual identity of this paper, kept the same as in its result figures: blue is the right action and every conforming outcome,
purple the forbidden control and every violation, slate for structure. Components: zones with a side marker and a left-aligned
title, cards with an inner header band, pill chips, letter tiles for the lettered options, slim dark arrows, real pages in a
browser window with a dark frame, and line icons. All sizes are in pixels on a canvas 1,800 px wide (the text width)."""
import base64, io, json, math, os
from PIL import Image, ImageFont

FD = "/usr/share/fonts/truetype/liberation/"
FONTS = {(False, False): FD + "LiberationSerif-Regular.ttf", (True, False): FD + "LiberationSerif-Bold.ttf", (False, True): FD + "LiberationSerif-Italic.ttf", (True, True): FD + "LiberationSerif-BoldItalic.ttf"}
MONO_FILE = FD + "LiberationMono-Regular.ttf"
SERIF = "Times New Roman, Liberation Serif, serif"; MONO = "Courier New, Liberation Mono, monospace"

INK, MUTED, LINE, PANEL = "#22262E", "#5F6673", "#C6CCD7", "#F5F7FB"
SLATE, SLATE_D, SLATE_L = "#56637A", "#343D4D", "#E4E8EF"
BLUE, BLUE_M, BLUE_L, BLUE_XL = "#3F6BD0", "#8FB3E6", "#DCE8F8", "#EEF4FC"
PURP, PURP_M, PURP_L, PURP_XL = "#7A5FCB", "#B9ADE8", "#E6E1F8", "#F4F2FC"
SKY, LILAC = "#6E9AD8", "#9B8FD8"                         # lighter members of the two families

_F = {}
def font(size, bold=False, italic=False, mono=False):
    k = (round(size * 4), bold, italic, mono)
    if k not in _F: _F[k] = ImageFont.truetype(MONO_FILE if mono else FONTS[(bold, italic)], max(4, int(round(size * 4))))
    return _F[k]
def tw(s, size, bold=False, italic=False, mono=False): return font(size, bold, italic, mono).getlength(s) / 4.0
def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def T(x, y, s, size=22, color=INK, anchor="start", bold=False, italic=False, mono=False):
    a = (' font-weight="bold"' if bold else "") + (' font-style="italic"' if italic else "")
    return f'<text xml:space="preserve" x="{x:.1f}" y="{y:.1f}" font-family="{MONO if mono else SERIF}" font-size="{size}" fill="{color}" text-anchor="{anchor}"{a}>{esc(s)}</text>'
def TS(x, y, segs, size=22, color=INK, anchor="start"):
    """one line of segments (text, style): style '' regular, 'b' bold, 'i' italic, 'm' mono, or a colour for regular text.
    The line is ONE text element with spans, so the renderer spaces the segments itself."""
    o = f'<text xml:space="preserve" x="{x:.1f}" y="{y:.1f}" font-family="{SERIF}" font-size="{size}" fill="{color}" text-anchor="{anchor}">'
    for t, k in segs:
        if k.startswith("#"): a = f' fill="{k}"'
        else: a = (' font-weight="bold"' if "b" in k else "") + (' font-style="italic"' if "i" in k else "") + (f' font-family="{MONO}"' if k == "m" else "")
        o += f"<tspan{a}>{esc(t)}</tspan>"
    return o + "</text>"
def TSW(segs, size=22):
    return sum(tw(t, size, bold="b" in k and not k.startswith("#"), italic="i" in k and not k.startswith("#"), mono=k == "m") for t, k in segs)

def rect(x, y, w, h, r=12, fill="white", stroke=LINE, sw=1.6, dash=None, op=None):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"'
            + (f' stroke-dasharray="{dash}"' if dash else "") + (f' fill-opacity="{op}"' if op is not None else "") + "/>")
def shadow(x, y, w, h, r=12):
    return "".join(f'<rect x="{x - k / 2 + 1:.1f}" y="{y + k:.1f}" width="{w + k - 2:.1f}" height="{h:.1f}" rx="{r + k / 2}" fill="#1B2433" opacity="{op}"/>' for k, op in ((7, 0.022), (4, 0.035), (2, 0.045)))
def line(x1, y1, x2, y2, color=LINE, w=1.6, dash=None, cap="round"):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="{cap}"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>"

def zone(x, y, w, h, title, color, sub=None):
    """a light zone with a marker bar and a left-aligned title at its top"""
    o = rect(x, y, w, h, r=22, fill=PANEL, stroke="#E2E7EF", sw=1.6)
    o += f'<rect x="{x + 24}" y="{y + 22}" width="7" height="30" rx="3.5" fill="{color}"/>' + T(x + 42, y + 46, title, 28, INK, bold=True)
    if sub: o += T(x + 42 + tw(title, 28, True) + 16, y + 45, sub, 20, MUTED)
    return o
def card(x, y, w, h, r=14, fill="white", stroke=LINE, sw=1.5): return shadow(x, y, w, h, r) + rect(x, y, w, h, r, fill, stroke, sw)
def hcard(x, y, w, h, title, color, hh=38, r=14, size=22):
    """a white card whose title sits on a coloured band inside its top edge"""
    o = shadow(x, y, w, h, r) + rect(x, y, w, h, r, "white", color, 1.8)
    o += f'<path d="M {x} {y + hh} L {x} {y + r} Q {x} {y} {x + r} {y} L {x + w - r} {y} Q {x + w} {y} {x + w} {y + r} L {x + w} {y + hh} Z" fill="{color}"/>'
    return o + T(x + 16, y + hh / 2 + size * 0.34, title, size, "white", bold=True)
def pill(x, y, s, size=20, fill=BLUE_L, color=INK, stroke=None, anchor="start", pad=11, bold=False, mono=False):
    """a pill chip whose text baseline is y; returns (svg, width)"""
    w = tw(s, size, bold, False, mono) + 2 * pad; h = size * 1.42; x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
    o = f'<rect x="{x0:.1f}" y="{y - size * 1.02:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="1.6"' if stroke else "") + "/>"
    return o + T(x0 + pad, y, s, size, color, "start", bold=bold, mono=mono), w
def P(*a, **k): return pill(*a, **k)[0]
TILE = {"right": (BLUE, "white", BLUE), "forb": (PURP, "white", PURP), "plain": ("white", INK, "#AEB6C3"), "dark": (SLATE_D, "white", SLATE_D), "soft_r": (BLUE_L, INK, BLUE), "soft_f": (PURP_L, INK, PURP)}
def tile(cx, cy, s, kind="plain", size=30):
    """a letter tile of a lettered option"""
    fill, col, st = TILE[kind]
    return rect(cx - size / 2, cy - size / 2, size, size, r=size * 0.22, fill=fill, stroke=st, sw=1.8) + T(cx, cy + size * 0.25, s, size * 0.70, col, "middle", bold=True)

def arrow(pts, color=SLATE, w=2.6, dash=None, head=11, r=12):
    """an orthogonal or straight arrow through pts, with rounded bends and a filled head"""
    d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"
    for k in range(1, len(pts) - 1):
        (xa, ya), (xb, yb), (xc, yc) = pts[k - 1], pts[k], pts[k + 1]; la = math.hypot(xb - xa, yb - ya); lc = math.hypot(xc - xb, yc - yb); rr = min(r, la / 2, lc / 2)
        p1 = (xb - (xb - xa) / la * rr, yb - (yb - ya) / la * rr); p2 = (xb + (xc - xb) / lc * rr, yb + (yc - yb) / lc * rr); d += f" L {p1[0]:.1f} {p1[1]:.1f} Q {xb:.1f} {yb:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    (xa, ya), (xb, yb) = pts[-2], pts[-1]; a = math.atan2(yb - ya, xb - xa); ex, ey = xb - head * 0.8 * math.cos(a), yb - head * 0.8 * math.sin(a); d += f" L {ex:.1f} {ey:.1f}"
    h1 = (xb - head * math.cos(a) + head * 0.48 * math.sin(a), yb - head * math.sin(a) - head * 0.48 * math.cos(a)); h2 = (xb - head * math.cos(a) - head * 0.48 * math.sin(a), yb - head * math.sin(a) + head * 0.48 * math.cos(a))
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>"
            + f'<polygon points="{xb:.1f},{yb:.1f} {h1[0]:.1f},{h1[1]:.1f} {h2[0]:.1f},{h2[1]:.1f}" fill="{color}"/>')
def chevron(x, y, s=9, color=SLATE, w=2.4): return f'<path d="M {x - s / 2:.1f} {y - s:.1f} L {x + s / 2:.1f} {y:.1f} L {x - s / 2:.1f} {y + s:.1f}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'
def bracket(x0, x1, y, color, up=True, w=2.4, t=9):
    """a horizontal bracket over [x0, x1] at y, its ends pointing down (up=True means the bracket sits above its content)"""
    d = t if up else -t
    return f'<path d="M {x0:.1f} {y + d:.1f} L {x0:.1f} {y:.1f} L {x1:.1f} {y:.1f} L {x1:.1f} {y + d:.1f}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'

# ---------------------------------------------------------------- icons (line style, one stroke weight)
def i_check(cx, cy, r=11, color=BLUE):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/><path d="M {cx - r * 0.45:.1f} {cy + r * 0.02:.1f} L {cx - r * 0.1:.1f} {cy + r * 0.38:.1f} L {cx + r * 0.5:.1f} {cy - r * 0.34:.1f}" fill="none" stroke="white" stroke-width="{r * 0.24:.1f}" stroke-linecap="round" stroke-linejoin="round"/>'
def i_ban(cx, cy, r=11, color=PURP):
    k = r * 0.62
    return f'<circle cx="{cx}" cy="{cy}" r="{r - 1.4:.1f}" fill="white" stroke="{color}" stroke-width="2.8"/><line x1="{cx - k:.1f}" y1="{cy - k:.1f}" x2="{cx + k:.1f}" y2="{cy + k:.1f}" stroke="{color}" stroke-width="2.8" stroke-linecap="round"/>'
def i_cross(cx, cy, r=11, color="#9AA3B2"):
    k = r * 0.42
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/><path d="M {cx - k:.1f} {cy - k:.1f} L {cx + k:.1f} {cy + k:.1f} M {cx + k:.1f} {cy - k:.1f} L {cx - k:.1f} {cy + k:.1f}" stroke="white" stroke-width="{r * 0.24:.1f}" stroke-linecap="round"/>'
def i_cursor(x, y, s=1.0, color=SLATE_D):
    """the pointer of the agent, its tip at (x, y)"""
    pts = [(0, 0), (0, 17), (4.6, 13.2), (7.8, 20.6), (10.8, 19.3), (7.6, 12.1), (13.2, 12.1)]
    return f'<polygon points="{" ".join(f"{x + px * s:.1f},{y + py * s:.1f}" for px, py in pts)}" fill="{color}" stroke="white" stroke-width="{1.7 * s:.1f}" stroke-linejoin="round"/>'
def i_lock(cx, cy, s=26, color=PURP):
    w, h = s * 0.70, s * 0.52; x, y = cx - w / 2, cy - h / 2 + s * 0.16
    return (f'<path d="M {cx - w * 0.30:.1f} {y:.1f} L {cx - w * 0.30:.1f} {y - s * 0.20:.1f} A {w * 0.30:.1f} {w * 0.30:.1f} 0 0 1 {cx + w * 0.30:.1f} {y - s * 0.20:.1f} L {cx + w * 0.30:.1f} {y:.1f}" fill="none" stroke="{color}" stroke-width="2.6"/>'
            + rect(x, y, w, h, r=4, fill=color, stroke=color, sw=1) + f'<circle cx="{cx}" cy="{y + h / 2:.1f}" r="2.6" fill="white"/>')
def i_chip(cx, cy, s=64, color=SLATE_D):
    """the model under test: a chip with pins and a small spark"""
    o = ""; h = s / 2
    for k in (-0.5, 0, 0.5):
        o += line(cx + k * h, cy - h - 7, cx + k * h, cy - h, color, 2.6) + line(cx + k * h, cy + h, cx + k * h, cy + h + 7, color, 2.6) + line(cx - h - 7, cy + k * h, cx - h, cy + k * h, color, 2.6) + line(cx + h, cy + k * h, cx + h + 7, cy + k * h, color, 2.6)
    o += rect(cx - h, cy - h, s, s, r=9, fill=color, stroke=color, sw=1) + rect(cx - h * 0.62, cy - h * 0.62, s * 0.62, s * 0.62, r=5, fill="white", stroke="white", sw=1, op=0.14)
    k = s * 0.17
    return o + f'<path d="M {cx} {cy - k * 1.5:.1f} Q {cx + k * 0.3:.1f} {cy - k * 0.3:.1f} {cx + k * 1.5:.1f} {cy} Q {cx + k * 0.3:.1f} {cy + k * 0.3:.1f} {cx} {cy + k * 1.5:.1f} Q {cx - k * 0.3:.1f} {cy + k * 0.3:.1f} {cx - k * 1.5:.1f} {cy} Q {cx - k * 0.3:.1f} {cy - k * 0.3:.1f} {cx} {cy - k * 1.5:.1f} Z" fill="white"/>'
def i_pages(cx, cy, s=34, color=SLATE):
    """two overlapping pages, the front one with an empty field"""
    w, h = s * 0.62, s * 0.80
    return (rect(cx - w / 2 - 7, cy - h / 2 - 5, w, h, r=4, fill="white", stroke=color, sw=2.2) + rect(cx - w / 2 + 5, cy - h / 2 + 4, w, h, r=4, fill="white", stroke=color, sw=2.2)
            + line(cx - w / 2 + 10, cy - h / 2 + 13, cx + w / 2, cy - h / 2 + 13, color, 2) + rect(cx - w / 2 + 9, cy - h / 2 + 19, w - 9, 9, r=3, fill="white", stroke=PURP, sw=2))
def i_eraser(cx, cy, s=30, color=SLATE):
    return f'<g transform="rotate(-35 {cx} {cy})">' + rect(cx - s * 0.5, cy - s * 0.22, s, s * 0.44, r=4, fill="white", stroke=color, sw=2.4) + rect(cx - s * 0.5, cy - s * 0.22, s * 0.42, s * 0.44, r=4, fill=color, stroke=color, sw=2.4) + "</g>"

# ---------------------------------------------------------------- real pages
CUR = os.environ.get("WC_CURATED", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "curated"))
_C = None
def case(sid):
    global _C
    if _C is None: _C = {c["sid"]: c for c in json.load(open(f"{CUR}/cases.json", encoding="utf-8"))["cases"]}
    return _C[sid]
def page(sid): return case(sid), Image.open(f"{CUR}/img/{sid}.jpg").convert("RGB")
def window(sid, win, out_w=520):
    c, im = page(sid); sx, sy = im.width / c["crop"][2], im.height / c["crop"][3]; cr = im.crop((int(win[0] * sx), int(win[1] * sy), int(win[2] * sx), int(win[3] * sy)))
    return cr.resize((out_w, int(out_w * cr.height / cr.width)), Image.LANCZOS)
_CL = [0]
def image(x, y, w, h, im, r=4, stroke=None, sw=1.4):
    b = io.BytesIO(); im.save(b, "JPEG", quality=92); _CL[0] += 1; cid = f"wcclip{_CL[0]}"
    o = f'<defs><clipPath id="{cid}"><rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}"/></clipPath></defs><image x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" href="data:image/jpeg;base64,{base64.b64encode(b.getvalue()).decode()}" clip-path="url(#{cid})" preserveAspectRatio="none"/>'
    return o + (rect(x, y, w, h, r, "none", stroke, sw) if stroke else "")
def browser(x, y, w, sid, win, url="", bar=24):
    """a browser window with a dark frame showing the part win of a real page. Returns (svg, height, to_xy) where to_xy maps a point
    of the page (in the pixel grid of the option boxes) to the canvas."""
    cr = window(sid, win, out_w=int(w * 2.4)); iw = w - 6; ih = iw * cr.height / cr.width; h = bar + ih + 3
    o = shadow(x, y, w, h, 11) + rect(x, y, w, h, 11, "white", SLATE_D, 2.4)
    o += f'<path d="M {x + 1.2} {y + bar} L {x + 1.2} {y + 11} Q {x + 1.2} {y + 1.2} {x + 11} {y + 1.2} L {x + w - 11} {y + 1.2} Q {x + w - 1.2} {y + 1.2} {x + w - 1.2} {y + 11} L {x + w - 1.2} {y + bar} Z" fill="{SLATE_D}"/>'
    for k in range(3): o += f'<circle cx="{x + 14 + k * 12}" cy="{y + bar / 2 + 0.6}" r="3.3" fill="#8794AB"/>'
    o += rect(x + 54, y + 5, w - 68, bar - 10, r=(bar - 10) / 2, fill="#4A566B", stroke="none", sw=0)
    if url: o += T(x + 66, y + bar / 2 + 4.2, url, 12, "#D7DDE8", mono=True)
    o += image(x + 3, y + bar, iw, ih, cr, r=3)
    kx, ky = iw / (win[2] - win[0]), ih / (win[3] - win[1])
    return o, h, (lambda px, py: (x + 3 + (px - win[0]) * kx, y + bar + (py - win[1]) * ky)), (kx, ky)
def mark(to, k, box, color, pad=2.5, sw=3.4, dash=None):
    """the outline of a control on a page shown by browser()"""
    (x, y) = to(box[0], box[1]); return rect(x - pad, y - pad, box[2] * k[0] + 2 * pad, box[3] * k[1] + 2 * pad, r=5, fill="none", stroke=color, sw=sw, dash=dash)

def svg_doc(W, H, body): return f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect x="0" y="0" width="{W}" height="{H}" fill="white"/>' + body + "</svg>"
def write(name, W, H, S, dst=None, preview_w=1700):
    import cairosvg, shutil
    here = os.path.dirname(os.path.abspath(__file__)); svg = svg_doc(W, H, "".join(S))
    open(os.path.join(here, name + ".svg"), "w", encoding="utf-8").write(svg); cairosvg.svg2pdf(bytestring=svg.encode(), write_to=os.path.join(here, name + ".pdf"))
    cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(here, name + "_preview.png"), output_width=preview_w)
    if dst: os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True); shutil.copy(os.path.join(here, name + ".pdf"), dst)
    print(name, "written")
