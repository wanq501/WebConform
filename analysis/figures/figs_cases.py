# -*- coding: utf-8 -*-
"""Screenshot comparison figures of WebConform, built from the curated export of Atelier (curated/cases.json + curated/img/*.jpg).

    python figs_cases.py <path to the curated folder>

Every case is one panel of the usual width (four per row): the page crop around the controls that matter, with the right control
(the demonstrated one, or the erased input of an erased state) boxed in green and the forbidden commit control in red; under it the task
and one chip per model coloured by its S0 decision (red forbidden commit, green demonstrated control, light grey another control,
grey no action). A counterfactual pair takes two neighbouring panels, the filled state and the erased state.
Figures written to out/: CaseA (R2 precondition), CaseB (R3, R1 and the commit control RC), CaseC and CaseD (counterfactual pairs),
each three rows of four panels with one legend strip, in the same palette and type as the result figures."""
import sys, os, json, textwrap
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from house import *
from figs_v5 import C_BLUE, C_GREY, C_GREY_L, FS_F, H_box, strip
C_GREEN, C_RED, C_RED_D = "#2F6BE0", "#8A46D8", "#5A2FA3"      # right control in blue, forbidden commit control in purple, both saturated to stand out on a page
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, FancyBboxPatch
from PIL import Image

CH_FULL = 1.24                                     # height of a case panel, inches
IMG_W, IMG_H = PW - 0.06, (PW - 0.06) * 0.40       # the page crop, same size and aspect in every panel
CODE = {"sonnet55": "Son", "gemini38": "Gem", "haiku55": "Hai", "gpt54mini": "GPT", "qwen35": "Q3.5", "qwen35_9b": "Q9B", "qwen3vl8b": "QVL", "internvl35": "IVL"}
REL = {"R1": "R1 safety", "R2": "R2 precondition", "R3": "R3 idempotency", "RC": "RC commit step", "CFF": "CF filled", "CFE": "CF erased"}

def boxes_of(case, W, H):
    """option boxes in image pixels: the stored screenshot is a downscaled copy of the crop the boxes refer to"""
    sx, sy = W / case["crop"][2], H / case["crop"][3]; sc = lambda b: [b[0] * sx, b[1] * sy, b[2] * sx, b[3] * sy] if b else None
    by = {o["letter"]: sc(o.get("box")) for o in case["options"]}; right_is_commit = case["relation"] in ("RC", "CFF")
    gold = [by[l] for l in case["gold"] if by.get(l)]; forb = [] if right_is_commit else [by[l] for l in case["forbidden"] if by.get(l)]
    return gold, forb, sc(case.get("field_box"))

MAX_W = 640                                        # widest window (image pixels) at which controls stay legible in a panel
FOCUS_FORBIDDEN = set()                            # probes shown around their forbidden controls only (filled from cases_choice.json)
def targets(case, W, H):
    gold, forb, field = boxes_of(case, W, H); ok = lambda b: b and b[0] < W and b[1] < H and b[2] > 0 and b[3] > 0 and b[0] + b[2] > 0 and b[1] + b[3] > 0
    gold = [b for b in gold if ok(b)]; forb = [b for b in forb if ok(b)]; ctr = lambda b: (b[0] + b[2] / 2, b[1] + b[3] / 2); bs = list(gold)
    if case["sid"] in FOCUS_FORBIDDEN and forb: return sorted(forb, key=lambda b: (b[1], b[0]))[:2]
    if field and ok(field): bs.append(field)
    if forb:
        if bs: gx, gy = np.mean([ctr(b)[0] for b in bs]), np.mean([ctr(b)[1] for b in bs]); bs.append(min(forb, key=lambda b: (ctr(b)[0] - gx) ** 2 + (ctr(b)[1] - gy) ** 2))
        else: bs.append(forb[0])
    return bs
def need_w(case, W, H):
    """width of the smallest window of the panel aspect that holds the target controls"""
    bs = targets(case, W, H); ar = IMG_H / IMG_W
    if not bs: return 1e9
    x0 = min(b[0] for b in bs); y0 = min(b[1] for b in bs); x1 = max(b[0] + b[2] for b in bs); y1 = max(b[1] + b[3] for b in bs); return max((x1 - x0) * 1.25 + 50, ((y1 - y0) * 1.25 + 50) / ar)
def roi(case, W, H, min_w=400):
    bs = targets(case, W, H); ar = IMG_H / IMG_W
    if not bs: return 0, 0, W, min(H, W * ar)
    x0 = min(b[0] for b in bs); y0 = min(b[1] for b in bs); x1 = max(b[0] + b[2] for b in bs); y1 = max(b[1] + b[3] for b in bs)
    w = min(max(min_w, need_w(case, W, H)), W, H / ar); h = w * ar
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; l = min(max(0, cx - w / 2), W - w); t = min(max(0, cy - h / 2), H - h); return l, t, w, h
def size_of(case, cdir):
    with Image.open(os.path.join(cdir, "img", case["sid"] + ".jpg")) as im: return im.size

def chip_color(d):
    if d is None: return "white", "#C9CED6", "#9AA3B0"
    if d.get("violation"): return C_RED, C_RED, "white"
    if d.get("correct"): return C_GREEN, C_GREEN, "white"
    if d.get("none"): return C_GREY, C_GREY, "white"
    return C_GREY_L, "#C9CED6", INK

def case_panel(case, models, cdir, name, letter_, sub=None, chips=True, win=None):
    CH = CH_FULL if chips else CH_FULL - 0.17
    fig = plt.figure(figsize=(PW, CH)); ax = fig.add_axes([0.03 / PW, (CH - 0.17 - IMG_H) / CH, IMG_W / PW, IMG_H / CH])
    fig.text(0.5, (CH - 0.03) / CH, sub or f"{case['relation']}, {case['website']}", ha="center", va="top", fontsize=FS_T, fontweight="bold", color=INK)
    im = Image.open(os.path.join(cdir, "img", case["sid"] + ".jpg")).convert("RGB"); W, H = im.size; l, t, w, h = win or roi(case, W, H)
    ax.imshow(im.crop((int(l), int(t), int(l + w), int(t + h))), extent=(l, l + w, t + h, t), aspect="auto", interpolation="lanczos")
    gold, forb, field = boxes_of(case, W, H)
    def draw(b, col, lw=1.2):
        if b: ax.add_patch(Rectangle((b[0] - 2.5, b[1] - 2.5), b[2] + 5, b[3] + 5, fill=False, ec=col, lw=lw, zorder=5))
    for b_ in forb: draw(b_, C_RED)
    for b_ in gold: draw(b_, C_GREEN)
    ax.set_xlim(l, l + w); ax.set_ylim(t + h, t); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_color("#8A8A8A"); s.set_linewidth(0.5)
    task = " ".join(case["task"].split()); task = task[0].upper() + task[1:]; task = textwrap.shorten(task, width=78, placeholder=" ..."); lines = textwrap.wrap(task, 40)[:2]
    fig.text(0.5, (CH - 0.20 - IMG_H) / CH, "\n".join(lines), ha="center", va="top", fontsize=5.0, style="italic", color="#3A3A3A", linespacing=1.1)
    cax = fig.add_axes([0.03 / PW, 0.135 / CH, IMG_W / PW, 0.15 / CH_FULL * CH_FULL / CH]); cax.set_xlim(0, len(models)); cax.set_ylim(0, 1); cax.axis("off")
    for i, m in enumerate(models if chips else []):
        d = (case["decisions"].get(m) or {}).get("s0"); fc, ec, tc = chip_color(d)
        cax.add_patch(FancyBboxPatch((i + 0.06, 0.08), 0.88, 0.84, boxstyle="round,pad=0,rounding_size=0.12", fc=fc, ec=ec, lw=0.4)); cax.text(i + 0.5, 0.5, CODE.get(m, m[:3]), ha="center", va="center", fontsize=4.4, color=tc, fontweight="bold")
    fig.text(0.5, 0.004, f"({letter_})", ha="center", va="bottom", fontsize=FS_L, color=INK); save(fig, name)

def violations(case, models): return sum(1 for m in models if ((case["decisions"].get(m) or {}).get("s0") or {}).get("violation"))
def pick(cases, models, rel, n, cdir, key=None):
    """the most telling cases of a relation whose controls fit a legible window: most models violating (or right, for RC), one per website first"""
    key = key or (lambda c: violations(c, models)); fit = lambda c: need_w(c, *size_of(c, cdir)) <= MAX_W
    pool = sorted((c for c in cases if c["relation"] == rel and fit(c)), key=lambda c: (-key(c), c["sid"])); out, seen = [], set()
    for c in pool:
        if c["website"] not in seen: out.append(c); seen.add(c["website"])
    for c in pool:
        if c not in out: out.append(c)
    return out[:n]

def draw_boxes(ax, case, W, H, lw=1.3):
    gold, forb, field = boxes_of(case, W, H)
    for b_, col in [(x, C_RED) for x in forb] + [(x, C_GREEN) for x in gold]: ax.add_patch(Rectangle((b_[0] - 2.5, b_[1] - 2.5), b_[2] + 5, b_[3] + 5, fill=False, ec=col, lw=lw, zorder=5))

def pair_real(f, e, cdir, name="FigM3"):
    """the counterfactual pair of the method section on a real page: the recorded state and the erased state, same window"""
    Wf, Hf = TEXTW, 1.72; iw = 2.38; ar = 0.50; ih = iw * ar; fig = plt.figure(figsize=(Wf, Hf)); W, H = size_of(e, cdir)
    bs = targets(e, W, H); x0 = min(b[0] for b in bs); y0 = min(b[1] for b in bs); x1 = max(b[0] + b[2] for b in bs); y1 = max(b[1] + b[3] for b in bs)
    w = max(520, (x1 - x0) * 1.5 + 80); h = w * ar; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; l = min(max(0, cx - w / 2), W - w); t = min(max(0, cy - h * 0.42), H - h)
    for k, (c, x) in enumerate(((f, 0.05), (e, Wf - iw - 0.05))):
        ax = fig.add_axes([x / Wf, 0.30 / Hf, iw / Wf, ih / Hf]); im = Image.open(os.path.join(cdir, "img", c["sid"] + ".jpg")).convert("RGB")
        ax.imshow(im.crop((int(l), int(t), int(l + w), int(t + h))), extent=(l, l + w, t + h, t), aspect="auto", interpolation="lanczos"); draw_boxes(ax, c, W, H, lw=1.5)
        ax.set_xlim(l, l + w); ax.set_ylim(t + h, t); ax.set_xticks([]); ax.set_yticks([])
        for s_ in ax.spines.values(): s_.set_color("#8A8A8A"); s_.set_linewidth(0.6)
        fig.text((x + iw / 2) / Wf, (0.30 + ih + 0.05) / Hf, ("Recorded state $s_K$ (CFF)", "Erased state $\\tilde{s}_K$ (CFE)")[k], ha="center", va="bottom", fontsize=FS_T, fontweight="bold", color=INK)
        fig.text((x + iw / 2) / Wf, 0.20 / Hf, ("The commit control is the correct action", "The commit is premature, the erased input is the correct action")[k], ha="center", va="top", fontsize=6.0, fontweight="bold", color=(C_GREEN, C_RED_D)[k])
    from matplotlib.patches import FancyArrowPatch
    ax0 = fig.add_axes([0, 0, 1, 1]); ax0.set_xlim(0, Wf); ax0.set_ylim(0, Hf); ax0.axis("off"); ax0.patch.set_alpha(0)
    ax0.add_patch(FancyArrowPatch((0.05 + iw + 0.06, 0.30 + ih / 2), (Wf - iw - 0.11, 0.30 + ih / 2), arrowstyle="simple,head_width=8,head_length=5,tail_width=3.5", fc="#C9D3E3", ec="#73829C", lw=0.6))
    ax0.text(Wf / 2, 0.30 + ih / 2 + 0.16, "erase one\nfilled input", ha="center", va="bottom", fontsize=5.6, color=INK, linespacing=1.05)
    save(fig, name)

def main(cdir):
    D = json.load(open(os.path.join(cdir, "cases.json"), encoding="utf-8")); models = [m for m in ORDER if m in [x["tag"] for x in D["models"]]]; by = {c["sid"]: c for c in D["cases"]}; L = "abcdefghijkl"
    CH_ = json.load(open(os.path.join(HERE, "cases_choice.json")))            # the selection made after looking at every candidate
    FOCUS_FORBIDDEN.update(CH_.get("focus_forbidden", []))
    A = [by[s] for s in CH_["A"]][:12]; B = [by[s] for s in CH_["B"]][:12]; P = [(by["CFF_" + s[4:]], by[s]) for s in CH_["P"]]
    for c, l in zip(A, L): case_panel(c, models, cdir, f"CaseA{l}", l)
    for c, l in zip(B, L): case_panel(c, models, cdir, f"CaseB{l}", l)
    for fig, chunk in (("CaseC", P[:6]), ("CaseD", P[6:10])):
        for k, (f, e) in enumerate(chunk):
            win = roi(e, *size_of(e, cdir))                 # one window for both states, around the erased input and the commit control
            case_panel(f, models, cdir, f"{fig}{L[2 * k]}", L[2 * k], sub=f"Filled, {f['website']}", win=win); case_panel(e, models, cdir, f"{fig}{L[2 * k + 1]}", L[2 * k + 1], sub=f"Erased, {e['website']}", win=win)
    hs = [Patch(fc="none", ec=C_GREEN, lw=1.1, label="Correct control (demonstrated, or the erased input)"), Patch(fc="none", ec=C_RED, lw=1.1, label="Forbidden commit control"),
          H_box(C_GREEN, "none", "MLLM chose the correct control"), H_box(C_RED, "none", "Forbidden commit"), H_box(C_GREY_L, "#C9CED6", "Another control"), H_box(C_GREY, "none", "No action")]
    for fig in ("CaseA", "CaseB", "CaseC", "CaseD"): strip(fig + "_legend", rows=[hs[:2], hs[2:]])
    # dataset examples: one probe per relation and two pairs, without the model chips
    ex = [(by[CH_["B"][4]], "R1 safety"), (by[CH_["A"][0]], "R2 precondition"), (by[CH_["B"][0]], "R3 idempotency"), (by[CH_["B"][6]], "RC commit step")]
    for (c, ttl), l in zip(ex, "abcd"): case_panel(c, models, cdir, f"Ex{l}", l, sub=ttl, chips=False)
    for k, sid in enumerate((CH_["P"][2], CH_["P"][4])):
        f, e = by["CFF_" + sid[4:]], by[sid]; win = roi(e, *size_of(e, cdir))
        case_panel(f, models, cdir, f"Ex{'efgh'[2 * k]}", "efgh"[2 * k], sub="CF pair, filled", chips=False, win=win); case_panel(e, models, cdir, f"Ex{'efgh'[2 * k + 1]}", "efgh"[2 * k + 1], sub="CF pair, erased", chips=False, win=win)
    strip("Ex_legend", hs[:2])
    pair_real(by["CFF_" + CH_["P"][3][4:]], by[CH_["P"][3]], cdir)
    json.dump({"CaseA": [c["sid"] for c in A], "CaseB": [c["sid"] for c in B], "CaseC": [e["sid"] for _, e in P[:6]], "CaseD": [e["sid"] for _, e in P[6:10]]}, open(os.path.join(OUT, "cases_selected.json"), "w"), indent=1)
    print("case figures written: CaseA 12, CaseB 12, CaseC 6 pairs, CaseD 6 pairs, Ex 8, FigM3 | models", models)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("WC_CURATED", os.path.join(ROOT, "..", "data", "curated")))
