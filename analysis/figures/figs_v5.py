# -*- coding: utf-8 -*-
"""WebConform 2D result figures, version 5. ONE design system for every panel.

Geometry   every panel is 1.322 x 1.40 in (four per row) with the SAME axes rectangle: 0.40 in left, 0.05 in right,
           0.36 in bottom, 0.26 in top, so the axes boxes of all panels of the paper line up. Title, finding line, axis
           labels and panel letter sit at fixed positions. Waffles are drawn inside the same rectangle.
Type       6 pt text, 6.5 pt bold titles, 5.6 pt finding line, 7 pt panel letters. No rotated tick labels.
Palette    BLUE  reference side (chance, S0, API models, the demonstrated control)
           RED   side of interest (observed, guard, local models) and every violation
           GREEN the right commit;  GREY_L another control;  GREY no action or unchanged
Marks      one dot size (S_DOT) and one edge for all scatter dots, 1.0 pt fit lines, 0.7 pt dashed reference lines."""
import sys, os, math, json, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from house import *
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap

G2 = json.load(open(os.path.join(ROOT, "figdata2.json"), encoding="utf-8"))
O = ORDER; API = O[:5]; LOC = O[5:]; MM = ["haiku55", "qwen35_9b", "qwen3vl8b", "internvl35"]
# ---------------------------------------------------------------- design system
C_BLUE, C_BLUE_L = "#4A6FC4", "#C4D9F1"            # reference side: blue
C_RED, C_RED_L, C_RED_D = "#7A6FC9", "#E3E1F8", "#4F4699"     # side of interest and violations: purple (the names are historical)
C_GREEN = "#3F63B8"                                 # the right commit: deep blue
C_GREY, C_GREY_L, C_TIE = "#8E97A6", "#EEF1F5", "#C9CED6"
WIN = "#F4F3FC"                                    # region in which the side of interest is better
AXL, AXR, AXB, AXT = 0.40, 0.09, 0.36, 0.26        # the one axes rectangle, inches
AW, AH = PW - AXL - AXR, PH - AXB - AXT
S_DOT, LW_FIT, LW_REF = 7.0, 1.0, 0.7
FS_F = 5.6
REF = dict(color="#555555", lw=LW_REF, ls=(0, (3, 2)))

def P(title, xlabel=None, ylabel=None, grid="both", finding=None, red=True, axis=True):
    fig = plt.figure(figsize=(PW, PH)); ax = fig.add_axes([AXL / PW, AXB / PH, AW / PW, AH / PH])
    cx = (AXL + AW / 2) / PW
    fig.text(cx, (PH - 0.035) / PH, title, ha="center", va="top", fontsize=FS_T, fontweight="bold", color=INK)
    if finding: fig.text(cx, (PH - 0.150) / PH, finding, ha="center", va="top", fontsize=FS_F, color=C_RED_D if red else "#7A7A7A")
    if not axis: ax.axis("off"); return fig, ax
    for s in ax.spines.values(): s.set_color(SPINE); s.set_linewidth(0.6)
    ax.tick_params(colors=INK, length=2.0, width=0.5, pad=1.5)
    if grid: ax.grid(True, axis=grid, ls="-", color=GRIDC, lw=0.45); ax.set_axisbelow(True)
    if xlabel: ax.set_xlabel(xlabel, fontweight="bold", color=INK); ax.xaxis.set_label_coords(0.5, -0.132 / AH)
    if ylabel: ax.set_ylabel(ylabel, fontweight="bold", color=INK); ax.yaxis.set_label_coords(-0.315 / AW, 0.5)
    return fig, ax

def done(fig, name, l): fig.text((AXL + AW / 2) / PW, 0.006, f"({l})", ha="center", va="bottom", fontsize=FS_L, color=INK); save(fig, name)
def rows_y(ax, labels, divider=None):
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels); ax.set_ylim(len(labels) - 0.45, -0.55); ax.tick_params(axis="y", length=0)
    if divider is not None: ax.axhline(divider, color="#BFBFBF", lw=0.5, ls=(0, (2, 1.5)), zorder=1)
def note(ax, text, loc="upper left"):
    x, y, ha, va = {"upper left": (0.04, 0.96, "left", "top"), "upper right": (0.96, 0.96, "right", "top"), "lower right": (0.96, 0.05, "right", "bottom"), "lower left": (0.04, 0.05, "left", "bottom")}[loc]
    ax.text(x, y, text, transform=ax.transAxes, ha=ha, va=va, fontsize=FS_F - 0.2, color=INK, linespacing=1.15, zorder=10, bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#A8A8A8", lw=0.45, alpha=0.94))
def dots(ax, x, y, color, z=3, alpha=0.85): ax.scatter(x, y, s=S_DOT, color=color, alpha=alpha, edgecolor="white", linewidth=0.25, zorder=z)
def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float); r = float(np.corrcoef(x, y)[0, 1]); n = len(x); t = r * math.sqrt(max(n - 2, 1) / max(1e-12, 1 - r * r)); return r, math.erfc(abs(t) / math.sqrt(2))
def pfmt(p): return "$p$ < 0.001" if p < 0.001 else f"$p$ = {p:.3f}"          # three decimals, as in the text and the tables
def fitband(ax, x, y, col, xs):
    x, y = np.asarray(x, float), np.asarray(y, float); b, a = np.polyfit(x, y, 1); yh = a + b * xs; res = y - (a + b * x); s = math.sqrt((res ** 2).sum() / max(1, len(y) - 2))
    se = s * np.sqrt(1 / len(y) + (xs - x.mean()) ** 2 / max(1e-12, ((x - x.mean()) ** 2).sum()))
    ax.fill_between(xs, yh - 1.96 * se, yh + 1.96 * se, color=col, lw=0, alpha=0.18, zorder=2); ax.plot(xs, yh, color=col, lw=LW_FIT, zorder=5)
def strip(name, handles=None, rows=None): legend_strip(name, handles, rows=rows)
def H_box(fc, ec, label): return Patch(fc=fc, ec=ec, lw=0.6, label=label)
def H_dot(c, label): return Line2D([], [], ls="none", marker="o", ms=3.4, mfc=c, mec="white", mew=0.3, label=label)
def H_ref(label): return Line2D([], [], label=label, **REF)
def H_line(c, label): return Line2D([], [], color=c, lw=LW_FIT, label=label)

# ---------------------------------------------------------------- A: oracle validation (waffles, mirrored votes)
ORC = [("WebConform（本文判定器）", "WebConform", "wc"), ("元素准确率（选错即有害）", "Element accuracy", "ea"), ("风险标签（改状态即有害）", "Action-risk label", "rl"), ("风险标签 v2（非链接控件）", "Risk label with SCC", "rl2")]
WAF = {"tp": C_RED, "fn": C_BLUE, "fp": C_RED_L, "tn": C_GREY_L}
def waffle(ax, seq, colors, cols=20, rows=15):
    """squares filled row by row from the top left inside the common axes rectangle, top aligned"""
    cell = 1.0 / cols; ax.set_xlim(0, 1); ax.set_ylim(0, AH / AW); top = AH / AW
    for i, k in enumerate(seq):
        r, c = divmod(i, cols); ax.add_patch(Rectangle((c * cell + 0.1 * cell, top - (r + 1) * cell + 0.1 * cell), 0.8 * cell, 0.8 * cell, fc=colors[k], ec="none"))
    ax.set_aspect("equal", anchor="N")
def under(fig, text): fig.text((AXL + AW / 2) / PW, (AXB - 0.105) / PH, text, ha="center", va="top", fontsize=FS_F, color="#5A5A5A")

def fig_oracle():
    OSr = json.load(open(os.path.join(ROOT, "oracle_stats.json"), encoding="utf-8"))["r2"]            # validation round, decisions on main-set probes
    CFG = [("wc", "WebConform"), ("wc_nolink", "OSR without the SCC"), ("rl", "Action-risk label"), ("ea", "Element accuracy")]
    for (k, nm), l in zip(CFG, "abcd"):
        o = OSr[k]; fig, ax = P(nm, finding=f"precision {100 * o['precision']:.0f}%, recall {100 * o['recall']:.0f}%", red=(k == "wc"), axis=False)
        waffle(ax, [c for c in ("tp", "fn", "fp", "tn") for _ in range(int(o[c]))], WAF); under(fig, f"{int(o['tp'])} hits, {int(o['fp'])} false alarms"); done(fig, f"A{l}", l)
    V = [v for v in OSr["votes"] if v["n"] == 3]
    for (k, nm), l in zip(CFG, "efgh"):
        f = [v["h"] for v in V if v[k]]; u = [v["h"] for v in V if not v[k]]; share = 100 * OSr[k]["precision"]      # the share of flagged decisions the panel calls harmful
        fig, ax = P(nm, "Judges voting harmful", "Decisions (%)", grid="y", finding=f"{share:.0f}% of its flags are harmful", red=(k == "wc"))
        hf = [100 * sum(1 for x in f if x == i) / max(1, len(f)) for i in range(4)]; hu = [100 * sum(1 for x in u if x == i) / max(1, len(u)) for i in range(4)]
        ax.bar(range(4), hf, 0.72, color=C_RED_L, edgecolor=C_RED, lw=0.6, zorder=3); ax.bar(range(4), [-x for x in hu], 0.72, color=C_BLUE_L, edgecolor=C_BLUE, lw=0.6, zorder=3); ax.axhline(0, color=SPINE, lw=0.6, zorder=4)
        ax.set_xticks(range(4)); ax.set_xlim(-0.6, 3.6); ax.set_ylim(-110, 110); ax.set_yticks([-100, -50, 0, 50, 100]); ax.set_yticklabels(["100", "50", "0", "50", "100"])
        note(ax, f"flagged {len(f)}", "upper right"); note(ax, f"not flagged {len(u)}", "lower right"); done(fig, f"A{l}", l)
    strip("A_legend", rows=[[H_box(WAF["tp"], "none", "Hit, flagged and harmful"), H_box(WAF["fn"], "none", "Miss"), H_box(WAF["fp"], "none", "False alarm"), H_box(WAF["tn"], "none", "Not flagged, benign")],
                            [H_box(C_RED_L, C_RED, "Decisions the oracle flags, upward"), H_box(C_BLUE_L, C_BLUE, "Decisions it does not flag, downward")]])

# ---------------------------------------------------------------- B: per website (horizontal box + jitter, grouped scatter)
def sites(m, need): return [v for v in G2["site"][m].values() if v[need] >= (3 if need == "n_c" else 8)]
def fig_site():
    def hbox(l, title, val, xlabel, xlim, need, finding, red=True, ticks=None):
        fig, ax = P(title, xlabel, grid="x", finding=finding, red=red); rng = np.random.default_rng(1)
        for i, m in enumerate(O):
            xs = np.array([val(v) for v in sites(m, need)], float); xs = xs[np.isfinite(xs)]; col, lc = (C_BLUE, C_BLUE_L) if m in API else (C_RED, C_RED_L)
            bp = ax.boxplot([xs], positions=[i], widths=0.62, orientation="horizontal", patch_artist=True, showfliers=False, medianprops=dict(color=col, lw=1.0), whiskerprops=dict(color=col, lw=0.6), capprops=dict(color=col, lw=0.6), zorder=3)
            for b in bp["boxes"]: b.set_facecolor(lc); b.set_edgecolor(col); b.set_linewidth(0.6)
            ax.scatter(xs, i + rng.uniform(-0.2, 0.2, len(xs)), s=1.6, color="#4A4A4A", alpha=0.40, lw=0, zorder=4)
        rows_y(ax, [MSHORT[m] for m in O], 4.5); ax.set_xlim(*xlim)
        if ticks: ax.set_xticks(ticks)
        done(fig, f"B{l}", l)
    n_c, n_r, n_a = len(sites(O[0], "n_c")), len(sites(O[0], "n_r1")), len(sites(O[0], "n"))
    hbox("a", "R1 safety", lambda v: 100 * v["v_r1"] / v["n_r1"], "Violation rate (%)", (-0.4, 12), "n_r1", f"near zero, {n_r} websites", ticks=[0, 5, 10])
    hbox("b", "Commit relations", lambda v: 100 * v["v_c"] / v["n_c"], "Violation rate (%)", (-3, 103), "n_c", "local models higher", ticks=[0, 50, 100])
    hbox("c", "Chance level", lambda v: 100 * v["ch_c"] / v["n_c"], "Chance (%)", (-1.5, 43), "n_c", f"same {n_c} websites for all", red=False, ticks=[0, 20, 40])
    hbox("d", "Element accuracy", lambda v: 100 * v["acc"] if v["acc"] is not None else float("nan"), "Accuracy (%)", (-3, 103), "n", f"{n_a} websites", red=False, ticks=[0, 50, 100])
    def grouped(l, title, xv, yv, xlabel, ylabel, need, xlim, ylim, finding, red=True, diag=False, xt=None, yt=None):
        fig, ax = P(title, xlabel, ylabel, finding=finding, red=red); txt = []
        if diag: ax.plot([xlim[0], xlim[1]], [xlim[0], xlim[1]], zorder=2, **REF)
        for ms, col, lab in ((API, C_BLUE, "API"), (LOC, C_RED, "Local")):
            xs = np.array([xv(v) for m in ms for v in sites(m, need)], float); ys = np.array([yv(v) for m in ms for v in sites(m, need)], float); ok = np.isfinite(xs) & np.isfinite(ys); xs, ys = xs[ok], ys[ok]
            dots(ax, xs, ys, col, alpha=0.55); fitband(ax, xs, ys, col, np.linspace(xlim[0], xlim[1], 60)); r, p = pearson(xs, ys); txt.append(f"{lab}  $r$ = {r:.2f}, {pfmt(p)}")
        note(ax, "\n".join(txt), "upper left"); ax.set_xlim(*xlim); ax.set_ylim(*ylim)
        if xt: ax.set_xticks(xt)
        if yt: ax.set_yticks(yt)
        done(fig, f"B{l}", l)
    acc = lambda v: 100 * v["acc"] if v["acc"] is not None else float("nan")
    grouped("e", "Chance and violations", lambda v: 100 * v["ch_c"] / v["n_c"], lambda v: 100 * v["v_c"] / v["n_c"], "Chance (%)", "Violation rate (%)", "n_c", (0, 40), (-4, 130), "local models above chance", diag=True, xt=[0, 20, 40], yt=[0, 50, 100])
    grouped("f", "Accuracy and violations", acc, lambda v: 100 * v["v_c"] / v["n_c"], "Accuracy (%)", "Violation rate (%)", "n_c", (0, 100), (-4, 130), "violations fall with accuracy", xt=[0, 50, 100], yt=[0, 50, 100])
    grouped("g", "Chance and R1", lambda v: 100 * v["ch_r1"] / v["n_r1"], lambda v: 100 * v["v_r1"] / v["n_r1"], "Chance (%)", "Violation rate (%)", "n_r1", (0, 12), (-0.5, 16), "all rates below chance", red=False, diag=True, xt=[0, 5, 10], yt=[0, 5, 10])
    grouped("h", "Accuracy and R1", acc, lambda v: 100 * v["v_r1"] / v["n_r1"], "Accuracy (%)", "Violation rate (%)", "n_r1", (0, 100), (-0.5, 16), "no trend, near zero", red=False, xt=[0, 50, 100], yt=[0, 5, 10])
    strip("B_legend", [H_box(C_BLUE_L, C_BLUE, "API models"), H_box(C_RED_L, C_RED, "Local models"), Line2D([], [], ls="none", marker="o", ms=2.2, mfc="#4A4A4A", mec="none", label="One website"), H_line(INK, "Linear fit with 95% band"), H_ref("Rate equal to chance")])

# ---------------------------------------------------------------- C: counterfactual pairs (paired scatter, stacked outcomes)
OUTC = {"commit_ok": C_GREEN, "commit": C_RED, "fill": C_BLUE, "other": C_GREY_L, "none": C_GREY}
def fig_cf():
    def pairs(l, title, get, xlabel, ylabel, word):
        pts = [get(r) for r in G2["pairs"].values()]; pts = [(100 * x, 100 * y) for x, y in pts if x is not None and y is not None]
        below = sum(1 for x, y in pts if y < x - 1e-9); above = sum(1 for x, y in pts if y > x + 1e-9)
        fig, ax = P(title, xlabel, ylabel, finding=word(below, above, len(pts)), red=above > below); rng = np.random.default_rng(3)
        ax.plot([0, 100], [0, 100], zorder=2, **REF)
        for x, y in pts: dots(ax, x + rng.uniform(-2, 2), y + rng.uniform(-2, 2), C_RED if y > x + 1e-9 else (C_BLUE if y < x - 1e-9 else C_TIE))
        ax.set_xlim(-6, 106); ax.set_ylim(-6, 106); ax.set_xticks([0, 50, 100]); ax.set_yticks([0, 50, 100]); done(fig, f"C{l}", l)
    w1 = lambda b, a, n: f"{b} of {n} pairs below"
    pairs("a", "All eight MLLMs", lambda r: r["all"], "Filled (%)", "Erased (%)", w1); pairs("b", "API models", lambda r: r["api"], "Filled (%)", "Erased (%)", w1); pairs("c", "Local models", lambda r: r["local"], "Filled (%)", "Erased (%)", w1)
    pairs("d", "With action history (S1)", lambda r: (r["mit"][1], r["e_s1"]), "Erased, S0 (%)", "Erased, S1 (%)", lambda b, a, n: f"{a} of {n} pairs above")
    def stacked(l, title, rows, finding, red, divider=None):
        fig, ax = P(title, "Pairs (%)", grid="x", finding=finding, red=red)
        for i, (lab, parts) in enumerate(rows):
            x = 0; tot = sum(v for _, v in parts) or 1
            for k, v in parts:
                w = 100 * v / tot
                if w > 0: ax.barh(i, w, 0.68, left=x, color=OUTC[k], edgecolor="white", linewidth=0.35, zorder=3); x += w
        rows_y(ax, [r[0] for r in rows], divider); ax.set_xlim(0, 100); ax.set_xticks([0, 50, 100]); done(fig, f"C{l}", l)
    def outcomes(m, st):
        f = FG["cf"][m]["flow"]; get = lambda side, k: sum(v for kk, v in f.items() if kk.split(">")[side] == k)
        return [("fill", get(1, "fill")), ("commit", get(1, "commit")), ("other", get(1, "other")), ("none", get(1, "none"))] if st == "CFE" else [("commit_ok", get(0, "commit")), ("other", get(0, "other")), ("none", get(0, "none"))]
    stacked("e", "Erased input, S0", [(MSHORT[m], outcomes(m, "CFE")) for m in O], "red, premature commit", True, 4.5)
    stacked("f", "Filled input, S0", [(MSHORT[m], outcomes(m, "CFF")) for m in O], "green, the right commit", False, 4.5)
    import analysis as A
    def rows_for(cond):
        rows = []
        for m in MM:
            for cc, lab in (("s0", MSHORT[m]), (cond, "+ " + SETS[cond])):
                c = collections.Counter()
                for s_, q in A.scr.items():
                    if q["relation"] != "CFE" or s_ not in A.main: continue        # the pairs kept for the test
                    p = A.pred(m, s_, cc)
                    if not p: continue
                    commit = p in [x for x in A.L(q["repeat_letters"]) if A.tags[s_].get(x) not in A.NAV]
                    c["commit" if commit else "fill" if p in A.L(q["gold_letters"]) else "none" if p == q["none_letter"] else "other"] += 1
                rows.append((lab, [(k, c.get(k, 0)) for k in ("fill", "commit", "other", "none")]))
        return rows
    stacked("g", "Erased input, history", rows_for("s1"), "history adds commits", True); stacked("h", "Erased input, check", rows_for("cvx"), "the check changes little", False)
    strip("C_legend", rows=[[H_dot(C_BLUE, "Pair below the diagonal"), H_dot(C_RED, "Pair above the diagonal"), H_dot(C_TIE, "Pair on the diagonal"), H_ref("Equal commit share")],
                            [H_box(C_GREEN, "none", "Correct commit"), H_box(C_RED, "none", "Premature commit"), H_box(C_BLUE, "none", "Fill the erased input"), H_box(C_GREY_L, "none", "Other control"), H_box(C_GREY, "none", "No action")]])

# ---------------------------------------------------------------- D: reasoning effort (densities) and accuracy against conformance (joint density)
def ks(a, b):
    a, b = np.sort(a), np.sort(b); allv = np.r_[a, b]; cdf = lambda s, x: np.searchsorted(s, x, side="right") / len(s); D = np.max(np.abs(cdf(a, allv) - cdf(b, allv)))
    ne = len(a) * len(b) / (len(a) + len(b)); lam = (math.sqrt(ne) + 0.12 + 0.11 / math.sqrt(ne)) * D
    return float(min(1, 2 * sum((-1) ** (k - 1) * math.exp(-2 * k * k * lam * lam) for k in range(1, 100))))
def fig_tokens():
    for (ms, t), l in zip(((["gemini38"], "Gemini 3.8 Flash"), (["haiku55"], "Claude Haiku 5.5"), (["gpt54mini"], "GPT-5.4 mini"), (["gemini38", "haiku55", "gpt54mini"], "Three models pooled")), "abcd"):
        v = np.concatenate([np.array([x[0] for x in G2["tok"][m]["v"]], float) for m in ms]); g = np.concatenate([np.array([x[0] for x in G2["tok"][m]["g"]], float) for m in ms]); p = ks(v, g)
        fig, ax = P(t, "Reasoning tokens", "Density", grid="x", finding="same effort as correct decisions" if p > 0.05 else "effort differs", red=False)
        hi = float(np.percentile(np.r_[v, g], 96)); grid = np.linspace(0, hi, 200); zmax = 0
        for d, col, fc in ((g, C_BLUE, C_BLUE_L), (v, C_RED, C_RED_L)):
            dd = d[d <= hi]; bw = 1.06 * dd.std() * len(dd) ** (-0.2); z = np.exp(-0.5 * ((grid[:, None] - dd[None, :]) / bw) ** 2).sum(1) / (len(dd) * bw * math.sqrt(2 * math.pi)); zmax = max(zmax, z.max())
            ax.fill_between(grid, 0, z, color=fc, alpha=0.65, lw=0, zorder=2); ax.plot(grid, z, color=col, lw=LW_FIT, zorder=3); ax.axvline(float(np.median(d)), color=col, lw=LW_REF, ls=(0, (3, 2)), zorder=4)
        ax.set_ylim(-0.20 * zmax, 1.55 * zmax)
        for d, col, y0 in ((g, C_BLUE, -0.18 * zmax), (v, C_RED, -0.095 * zmax)): ax.vlines(d[d <= hi], y0, y0 + 0.07 * zmax, color=col, lw=0.22, alpha=0.6, zorder=2)
        ax.axhline(0, color=SPINE, lw=0.5, zorder=5); ax.set_yticks([]); ax.set_xlim(0, hi); ax.locator_params(axis="x", nbins=3)
        note(ax, f"median shift {np.median(v) - np.median(g):+.1f}\nKS test {pfmt(p)}", "upper right"); done(fig, f"D{l}", l)
    cmap = LinearSegmentedColormap.from_list("jd", ["#FFFFFF", "#E6EEF9", "#C4D9F1", "#90B7E2", "#4A6FC4", "#2C4A9A"])
    for (splits, t), l in zip(((("test_task",), "Cross-task"), (("test_website",), "Cross-website"), (("test_domain",), "Cross-domain"), (("test_task", "test_website", "test_domain"), "All splits")), "efgh"):
        xs, ys = [], []
        for m in O:
            for v in G2["site"][m].values():
                if v["n_c"] >= 2 and v["acc"] is not None and v["split"] in splits: xs.append(100 * v["acc"]); ys.append(100 - 100 * v["v_c"] / v["n_c"])
        xs, ys = np.array(xs), np.array(ys); r, p = pearson(xs, ys)
        fig, ax = P(t, "Accuracy (%)", "Conforming (%)", grid=None, finding=f"$r$ = {r:.2f}, {pfmt(p)}", red=p < 0.05)
        Hh, xe, ye = np.histogram2d(xs, ys, bins=[np.linspace(0, 100, 11), np.linspace(0, 100, 11)])
        im = ax.imshow(Hh.T, origin="lower", extent=(0, 100, 0, 100), cmap=cmap, aspect="auto", interpolation="nearest", zorder=1)
        b, a = np.polyfit(xs, ys, 1); xx = np.linspace(3, 97, 50); ax.plot(xx, np.clip(a + b * xx, 0, 100), color=C_RED, lw=LW_FIT, zorder=3)
        ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.set_xticks([0, 50, 100]); ax.set_yticks([0, 50, 100])
        cax = fig.add_axes([(AXL + AW - 0.36) / PW, (AXB + 0.075) / PH, 0.30 / PW, 0.035 / PH]); cb = fig.colorbar(im, cax=cax, orientation="horizontal"); cb.outline.set_linewidth(0.3)
        cb.ax.tick_params(labelsize=FS - 1.4, length=1, width=0.3, pad=0.6); cb.set_ticks([0, int(Hh.max())]); note(ax, f"n = {len(xs)}", "lower left"); done(fig, f"D{l}", l)
    strip("D_legend", rows=[[H_box(C_BLUE_L, C_BLUE, "Decisions on the demonstrated control"), H_box(C_RED_L, C_RED, "Forbidden commits"), H_ref("Median"), Line2D([], [], color=INK, lw=0.3, marker="|", ms=5, ls="none", label="One decision")],
                            [H_box("#93B6E2", "none", "MLLM and website pairs per cell"), H_line(C_RED, "Linear trend")]])

# ---------------------------------------------------------------- E: stability waffles
def fig_stab():
    col = {"x": C_BLUE, "v": C_RED, "g": C_GREEN, "o": C_GREY_L, "n": C_GREY}
    for m, l in zip(MM, "abcd"):
        runs = FG["runs"][m]; cats = ["x" if len(set(r)) > 1 else r[0] for r in runs]; seq = sorted(cats, key=lambda c: "xvgon".index(c)); ch = cats.count("x")
        fig, ax = P(MNAME[m], finding=f"{ch} of {len(seq)} decisions changed", red=ch > 10, axis=False); waffle(ax, seq, col, cols=16, rows=13)
        under(fig, f"{cats.count('v')} violations in all runs"); done(fig, f"E{l}", l)
    strip("E_legend", [H_box(C_BLUE, "none", "Decision changed between runs"), H_box(C_RED, "none", "Same violation in all runs"), H_box(C_GREEN, "none", "Demonstrated control in all runs"), H_box(C_GREY_L, "none", "Same other control"), H_box(C_GREY, "none", "No action")])

# ---------------------------------------------------------------- F: guards against S0, one dot per model and task
def fig_guards():
    import analysis as A
    def cells(c):
        T = collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0])
        for m in MM:
            for s in A.main:
                q = A.scr[s]; a, b = A.pred(m, s, "s0"), A.pred(m, s, c)
                if not a or not b: continue
                t = T[(m, q["annotation_id"])]
                if q["relation"] in ("R2", "R3", "CFE"): t[0] += 1; t[1] += a in A.viol_letters(q); t[2] += b in A.viol_letters(q)
                if q["relation"] in ("RC", "CFF"): t[3] += 1; t[4] += a in A.L(q["gold_letters"]); t[5] += b in A.L(q["gold_letters"])
        return list(T.values())
    for row, (kind, word, lets) in enumerate((("v", "violations", "abcd"), ("c", "correct commits", "efgh"))):
        for c, l in zip(("cvx", "cv", "s2", "rg"), lets):
            pts = [(100 * t[1] / t[0], 100 * t[2] / t[0]) for t in cells(c) if t[0]] if kind == "v" else [(100 * t[4] / t[3], 100 * t[5] / t[3]) for t in cells(c) if t[3]]
            better = sum(1 for x, y in pts if (y < x - 1e-9 if kind == "v" else y > x + 1e-9)); worse = sum(1 for x, y in pts if (y > x + 1e-9 if kind == "v" else y < x - 1e-9))
            fig, ax = P(f"{SETS[c]}, {word}", "S0 (%)", f"{SETS[c]} (%)", finding=f"{better} better, {worse} worse", red=better > worse); rng = np.random.default_rng(7)
            if kind == "v": ax.fill_between([-6, 106], [-6, -6], [-6, 106], color=WIN, lw=0, zorder=0)
            else: ax.fill_between([-6, 106], [-6, 106], [106, 106], color=WIN, lw=0, zorder=0)
            ax.plot([-6, 106], [-6, 106], zorder=2, **REF)
            for x, y in pts:
                good = (y < x - 1e-9) if kind == "v" else (y > x + 1e-9); bad = (y > x + 1e-9) if kind == "v" else (y < x - 1e-9)
                dots(ax, x + rng.uniform(-3.2, 3.2), y + rng.uniform(-3.2, 3.2), C_RED if good else (C_BLUE if bad else C_TIE), z=4 if (good or bad) else 3, alpha=0.8)
            ax.set_xlim(-6, 106); ax.set_ylim(-6, 106); ax.set_xticks([0, 50, 100]); ax.set_yticks([0, 50, 100]); done(fig, f"F{l}", l)
    strip("F_legend", [H_box(WIN, "#CFCBEF", "Region where the guardrail is better"), H_dot(C_RED, "Guardrail better"), H_dot(C_BLUE, "Guardrail worse"), H_dot(C_TIE, "Unchanged"), H_ref("No change")])

if __name__ == "__main__":
    which = sys.argv[1:] or ["oracle", "site", "cf", "tokens", "stab", "guards"]
    for w in which: globals()["fig_" + w]()
    print("v5 panels written:", which)
